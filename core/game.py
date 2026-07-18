"""
飞机大战 - 游戏主循环

整合所有模块，管理游戏状态和场景切换。

设计要点
--------
* ``Game`` 为单例（``_instance``），全局唯一实例 ``game`` 在模块加载时创建。
* 实体的 widget 挂载/卸载由 ``_attach_entity`` / ``_detach_entity`` 统一维护，
  使 widget 树与逻辑列表始终同步，避免每帧全量扫描清理僵尸 widget。
* 实体回收统一走 ``_recycle`` / ``_recycle_bullet``，保证
  「从逻辑列表移除 → 卸载 widget → 归还对象池」三步成对执行。
"""
import random
import time
import traceback
from enum import Enum
from typing import Optional

from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout

from config.settings import get_config
from core.pool import MultiTypePool
from entities.boss import Boss
from entities.bullet import Bullet
from entities.enemy import Enemy
from entities.explosion import Explosion
from entities.player import Player
from entities.powerup import PowerUp
from systems.achievement import achievement_manager
from systems.audio import audio_manager
from systems.collision import CollisionSystem
from systems.particle import particle_system
from systems.save import save_manager
from utils.helpers import chance, random_int
from utils.screen import screen, update_screen

# 武器等级 → 各枪口横向偏移（占屏幕宽度的比例）
# 1 级单发居中；2 级双发对称；3 级三发齐射。
_WEAPON_OFFSETS: dict[int, tuple[float, ...]] = {
    1: (0.0,),
    2: (-0.02, 0.02),
    3: (-0.03, 0.0, 0.03),
}

# 连击分数倍率门槛：自上而下匹配，首个命中的门槛生效。
# 例如连击 25 时命中 (20, 3) → 3 倍分数。
_COMBO_BONUS_TIERS: tuple[tuple[int, int], ...] = ((50, 5), (20, 3), (10, 2))

# 击杀类成就 ID：每次击杀统一推进这些累计型成就的进度。
_KILL_ACHIEVEMENTS: tuple[str, ...] = (
    'first_blood', 'killer_10', 'killer_100', 'killer_1000',
)


class GameState(Enum):
    """游戏状态枚举"""
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    GAME_OVER = 'game_over'


class Game:
    """
    游戏主类（单例模式）

    管理游戏状态、场景切换、实体生命周期。
    所有实体更新、碰撞分发、连击/震屏/道具掉落均在此协调。
    """

    _instance: Optional['Game'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 配置
        self.config = get_config()

        # 游戏状态
        self.state = GameState.MENU
        self.score = 0
        self.level = 1
        self.enemies_killed = 0
        self.boss_spawned = False

        # 实体集合（逻辑列表，widget 挂载状态与之一致）
        self.player: Optional[Player] = None
        self.enemies: list[Enemy] = []
        self.bullets: list[Bullet] = []
        self.powerups: list[PowerUp] = []
        self.explosions: list[Explosion] = []
        self.boss: Optional[Boss] = None

        # 对象池：子弹 / 敌机 / 道具复用，消除运行期 GC 抖动
        self.pools = MultiTypePool()
        self._setup_pools()

        # 碰撞系统（空间哈希 + 类型索引）
        self.collision = CollisionSystem()
        self._setup_collision_groups()

        # 计时器
        self.spawn_timer = 0.0
        self.shoot_timer = 0.0

        # 触摸控制
        self.touch_pos = None
        self.touch_offset = (0, 0)
        self.last_tap_time = 0.0

        # 根 widget 引用，用于挂载/卸载实体 widget 与屏幕震动
        self.root_widget: Optional[FloatLayout] = None

        # 屏幕震动
        self.shake_intensity = 0.0
        self.shake_decay = 0.85

        # 连击系统
        self.combo = 0
        self.combo_timer = 0.0
        self.combo_timeout = 1.5  # 秒内连续击杀算连击
        self.max_combo = 0

        # 碰撞检测复用缓冲区：每帧 clear+extend，避免反复分配新列表
        self._collision_entities: list = []

        # 绑定窗口大小变化
        Window.bind(on_resize=self._on_window_resize)

    def _setup_pools(self) -> None:
        """注册各实体类型的对象池并预创建初始对象。"""
        # 子弹池（玩家/敌方分别建池，acquire 时通过 reset 自动设定速度方向）
        self.pools.register('bullet_player', lambda: Bullet(is_player=True), initial_size=100)
        self.pools.register('bullet_enemy', lambda: Bullet(is_player=False), initial_size=50)

        # 敌机池（按类型分池，便于按类型归还）
        self.pools.register('enemy_normal', lambda: Enemy(enemy_type='normal'), initial_size=20)
        self.pools.register('enemy_fast', lambda: Enemy(enemy_type='fast'), initial_size=10)
        self.pools.register('enemy_tank', lambda: Enemy(enemy_type='tank'), initial_size=10)

        # 道具池
        self.pools.register('powerup', lambda: PowerUp(), initial_size=10)

    def _setup_collision_groups(self) -> None:
        """注册碰撞组：声明哪两类实体碰撞时调用哪个回调。"""
        self.collision.register_collision_group('bullet_player', 'enemy', self._on_bullet_hit_enemy)
        self.collision.register_collision_group('bullet_player', 'boss', self._on_bullet_hit_boss)
        self.collision.register_collision_group('bullet_enemy', 'player', self._on_bullet_hit_player)
        self.collision.register_collision_group('powerup', 'player', self._on_powerup_collected)

    def _on_window_resize(self, instance, width, height) -> None:
        """窗口大小变化处理：刷新屏幕适配器。"""
        update_screen()

    # ------------------------------------------------------------------
    # 实体 widget 树维护
    #
    # 实体在 spawn 时挂载、死亡/出界时卸载，widget 树始终与逻辑列表同步，
    # 消除 O(实体数) 的每帧扫描与 O(children) 的僵尸清理。
    # ------------------------------------------------------------------

    def _attach_entity(self, entity) -> None:
        """将实体挂到根 widget 树（若已挂载或无根则跳过），并刷新 z-order。"""
        rw = self.root_widget
        if rw is not None and entity.parent is None:
            rw.add_widget(entity)
            # 仅在挂载新实体时修正图层顺序，成本 = O(player + 爆炸 + hud) 远低于全量扫描
            rw._fix_z_order()

    def _detach_entity(self, entity) -> None:
        """从 widget 树卸载实体（幂等）。"""
        if entity.parent is not None:
            entity.parent.remove_widget(entity)

    def _recycle(self, entity, entity_list, pool_name: str) -> None:
        """统一回收实体：从逻辑列表移除 → 卸载 widget → 归还对象池。

        取代此前散落在各回调中的「remove + _detach_entity + pools.release」三连，
        保证三步始终成对执行，避免泄漏 widget 或对象池对象。
        各步骤均幂等：entity 不在列表中 / 无父 widget / 不在池的 active 集合中时安全跳过。
        """
        if entity in entity_list:
            entity_list.remove(entity)
        self._detach_entity(entity)
        self.pools.release(pool_name, entity)

    def _recycle_bullet(self, bullet: Bullet) -> None:
        """回收子弹（依据 ``is_player`` 选择对应对象池）。"""
        pool_name = 'bullet_player' if bullet.is_player else 'bullet_enemy'
        self._recycle(bullet, self.bullets, pool_name)

    def _fire_enemy_bullet(self, pos: tuple) -> None:
        """在指定左下角坐标生成一发敌方子弹并挂载（敌机/Boss 共用）。"""
        bullet = self.pools.acquire('bullet_enemy')
        bullet.pos = pos
        self.bullets.append(bullet)
        self._attach_entity(bullet)

    def start_game(self) -> None:
        """开始新游戏：重置状态、清空实体、创建玩家、播放背景音乐。"""
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.enemies_killed = 0
        self.boss_spawned = False

        # 清空所有实体（玩家由调用方单独挂载）
        self._clear_all_entities()

        # 创建玩家并定位到屏幕底部居中
        self.player = Player()
        self.player.pos = (
            screen.real_width / 2 - self.player.width / 2,
            screen.rel_h(0.12)
        )

        # 播放背景音乐
        if self.config.sound_enabled:
            audio_manager.play_music('bgm', loop=True)

    def pause_game(self) -> None:
        """暂停游戏"""
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
            audio_manager.pause_music()

    def resume_game(self) -> None:
        """恢复游戏"""
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
            audio_manager.resume_music()

    def game_over(self) -> None:
        """游戏结束：保存最高分、累加统计、停止音乐。"""
        self.state = GameState.GAME_OVER

        # 保存最高分（仅当刷新纪录时写入）
        save_manager.save_high_score(self.score)

        # 累加统计：max_level_reached 取历史最大值，避免重复读盘
        stats = save_manager.load_statistics()
        save_manager.update_statistics({
            'total_games': 1,
            'total_score': self.score,
            'max_level_reached': max(stats.get('max_level_reached', 0), self.level),
        })

        # 停止音乐
        audio_manager.stop_music()

    def update(self, dt: float) -> None:
        """
        游戏主更新循环

        Args:
            dt: 时间增量（秒）
        """
        if self.state != GameState.PLAYING:
            return

        # 更新计时器
        self.spawn_timer += dt
        self.shoot_timer += dt

        # 获取关卡配置
        level_config = self.config.get_level(self.level)

        # 生成敌机（Boss 出现后停止普通刷怪）
        if self.spawn_timer >= level_config.spawn_rate and not self.boss_spawned:
            self.spawn_timer = 0
            self._spawn_enemy(level_config.enemy_types)

        # 自动射击
        if self.shoot_timer >= self.config.shoot_cooldown:
            self.shoot_timer = 0
            self._player_shoot()

        # 更新各实体
        self._update_player(dt)
        self._update_enemies(dt)
        self._update_bullets(dt)
        self._update_powerups(dt)
        self._update_explosions(dt)

        # 更新Boss
        if self.boss:
            self._update_boss(dt)

        # 更新粒子与屏幕效果
        particle_system.update(dt)
        self._update_shake(dt)
        self._update_combo(dt)

        # 碰撞检测
        self._check_collisions()

        # 检查关卡进度（是否触发 Boss 战）
        self._check_level_progress(level_config)

    def _spawn_enemy(self, enemy_types: list[str]) -> None:
        """随机生成一只敌机并挂载。"""
        enemy_type = random.choice(enemy_types)
        pool_name = f'enemy_{enemy_type}'

        enemy = self.pools.acquire(pool_name)
        enemy.pos = (
            random_int(20, int(screen.real_width - enemy.width - 20)),
            screen.real_height
        )

        self.enemies.append(enemy)
        self._attach_entity(enemy)

    def _player_shoot(self) -> None:
        """玩家自动射击：按武器等级发射 1/2/3 发子弹。"""
        if not self.player:
            return

        weapon_level = min(self.player.weapon_level, 3)
        for offset in _WEAPON_OFFSETS.get(weapon_level, (0.0,)):
            bullet = self.pools.acquire('bullet_player')
            bullet.pos = (
                self.player.center_x - bullet.width / 2 + screen.rel_w(offset),
                self.player.top
            )
            self.bullets.append(bullet)
            self._attach_entity(bullet)

        # 播放射击音效
        audio_manager.play_sfx('shoot')

    def _update_player(self, dt: float) -> None:
        """更新玩家：跟随触摸位置平滑移动 + 状态计时。"""
        if not self.player:
            return

        # 触摸移动
        if self.touch_pos:
            target_x = self.touch_pos[0] - self.touch_offset[0]
            target_y = self.touch_pos[1] - self.touch_offset[1]
            self.player.move_to(target_x, target_y, smooth=True)

        self.player.update(dt)

    def _update_enemies(self, dt: float) -> None:
        """更新所有敌机：移动、射击、出界回收。"""
        for enemy in self.enemies[:]:
            enemy.update(dt)

            # 敌机射击：子弹居中于敌机底部
            if enemy.should_shoot():
                bullet = self.pools.acquire('bullet_enemy')
                bullet.pos = (enemy.center_x - bullet.width / 2, enemy.y)
                self.bullets.append(bullet)
                self._attach_entity(bullet)

            # 出界回收（margin 给出敌机高度余量，确保完全离开屏幕再回收）
            if not enemy.is_on_screen(margin=enemy.height):
                self._recycle(enemy, self.enemies, f'enemy_{enemy.enemy_type}')

    def _update_bullets(self, dt: float) -> None:
        """更新所有子弹：移动、出界回收。"""
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if not bullet.is_on_screen():
                self._recycle_bullet(bullet)

    def _update_powerups(self, dt: float) -> None:
        """更新所有道具：移动、出界回收。"""
        for powerup in self.powerups[:]:
            powerup.update(dt)
            if not powerup.is_on_screen():
                self._recycle(powerup, self.powerups, 'powerup')

    def _update_explosions(self, dt: float) -> None:
        """更新所有爆炸：推进动画，结束后卸载 widget。"""
        for explosion in self.explosions[:]:
            explosion.update(dt)
            if not explosion.active:
                self.explosions.remove(explosion)
                self._detach_entity(explosion)

    def _update_boss(self, dt: float) -> None:
        """更新Boss：移动、多发射点齐射。"""
        if not self.boss:
            return

        self.boss.update(dt)

        # Boss射击：按当前阶段在多个发射点生成子弹
        if self.boss.should_shoot():
            for pos in self.boss.get_shoot_positions():
                self._fire_enemy_bullet(pos)

    def _check_collisions(self) -> None:
        """收集活动实体 → 更新空间哈希 → 触发碰撞回调。

        复用 ``_collision_entities`` 缓冲区避免每帧分配新列表；
        碰撞异常被捕获并打印，避免单帧异常中断整个游戏循环。
        """
        entities = self._collision_entities
        entities.clear()
        if self.player:
            entities.append(self.player)
        entities.extend(self.enemies)
        entities.extend(self.bullets)
        entities.extend(self.powerups)
        if self.boss:
            entities.append(self.boss)

        self.collision.update(entities)
        try:
            self.collision.check_collisions()
        except Exception as e:
            print(f'[Game] 碰撞检测异常: {e}')
            traceback.print_exc()

    def _on_bullet_hit_enemy(self, bullet: Bullet, enemy: Enemy) -> None:
        """玩家子弹击中敌机：扣血、回收子弹、敌机死亡则计分/爆炸/掉落/成就。"""
        enemy.take_damage(bullet.damage)
        self._recycle_bullet(bullet)

        if not enemy.active:
            # 敌机死亡
            self._on_kill()
            self.score += enemy.score * self._combo_bonus()

            # 创建爆炸（必须在回收前读取 enemy 中心坐标）
            self._create_explosion(enemy.center, enemy.width)
            self._recycle(enemy, self.enemies, f'enemy_{enemy.enemy_type}')

            # 按掉落率概率生成道具
            if chance(self.config.powerup.drop_rate):
                self._spawn_powerup(enemy.center)

            # 播放音效
            audio_manager.play_sfx('explosion')

            # 推进所有累计型击杀成就
            for aid in _KILL_ACHIEVEMENTS:
                achievement_manager.increment_achievement(aid)

    def _on_bullet_hit_boss(self, bullet: Bullet, boss: Boss) -> None:
        """玩家子弹击中Boss：扣血、回收子弹、Boss死亡则大爆炸/进下一关/成就。"""
        boss.take_damage(bullet.damage)
        self._recycle_bullet(bullet)

        if not boss.active:
            # Boss死亡
            self.score += boss.score * self._combo_bonus()

            # 多重爆炸 + 粒子 + 震屏
            self._create_explosion(boss.center, boss.width * 1.5)
            self._create_explosion((boss.x, boss.center_y), boss.width * 0.6)
            self._create_explosion((boss.right, boss.center_y), boss.width * 0.6)
            particle_system.emit(boss.center_x, boss.center_y, 'explosion',
                                 count=40, spread=100, speed=200)
            self.trigger_shake(18.0)

            # 移除Boss（Boss不入池，仅卸载 widget）
            self._detach_entity(boss)
            self.boss = None
            self.boss_spawned = False

            # 进入下一关
            self.level += 1
            self.enemies_killed = 0

            # 播放音效
            audio_manager.play_sfx('boss_death')

            # 推进 Boss 击杀成就
            achievement_manager.increment_achievement('boss_first')
            achievement_manager.increment_achievement('boss_5')
            achievement_manager.increment_achievement('boss_10')

    def _on_bullet_hit_player(self, bullet: Bullet, player: Player) -> None:
        """敌方子弹击中玩家：扣血、断连击、震屏、死亡判定/复活。

        注意：``Player.take_damage`` 内部已处理「血量归零 → 扣命 → 复活回血」，
        此处保留对 ``player.health <= 0`` 的二次判定以兼容该流程，
        确保生命耗尽时正确触发 game_over（行为与原版一致）。
        """
        if player.shield or player.invincible:
            return

        self._recycle_bullet(bullet)

        # 玩家受伤
        player.take_damage()
        self.combo = 0  # 受伤断连击
        self.trigger_shake(4.0)

        # 播放音效
        audio_manager.play_sfx('hit')

        if player.health <= 0:
            player.lives -= 1
            if player.lives <= 0:
                self.game_over()
            else:
                # 复活：回满血并赋予短暂无敌
                player.health = player.max_health
                player.invincible = True
                player.invincible_time = self.config.player.invincible_time

    def _on_powerup_collected(self, powerup: PowerUp, player: Player) -> None:
        """收集道具：应用效果、回收道具、播放音效。"""
        powerup.apply(player)
        self._recycle(powerup, self.powerups, 'powerup')
        audio_manager.play_sfx('powerup')

    def _spawn_powerup(self, pos: tuple) -> None:
        """在指定中心坐标生成一个随机类型道具。"""
        powerup = self.pools.acquire('powerup')
        powerup_type = random.choice(self.config.powerup.types)
        powerup.setup_type(powerup_type)
        powerup.pos = (pos[0] - powerup.width / 2, pos[1] - powerup.height / 2)
        self.powerups.append(powerup)
        self._attach_entity(powerup)

    def _create_explosion(self, pos: tuple, size: float) -> None:
        """在指定位置创建爆炸效果并附加粒子。"""
        explosion = Explosion(pos=pos, size_ratio=size / screen.real_width)
        self.explosions.append(explosion)
        self._attach_entity(explosion)

        # 粒子效果
        particle_system.emit(pos[0], pos[1], 'explosion', count=15)

    def _check_level_progress(self, level_config) -> None:
        """检查关卡进度：击杀达标且尚未召唤 Boss 时召唤 Boss。"""
        if self.enemies_killed >= level_config.enemies_to_kill and not self.boss_spawned:
            self._spawn_boss()

    def _spawn_boss(self) -> None:
        """召唤Boss：定位到顶部居中、清空普通敌机、播放音效。"""
        self.boss_spawned = True
        self.boss = Boss(level=self.level)
        self.boss.pos = (
            screen.real_width / 2 - self.boss.width / 2,
            screen.real_height - self.boss.height - 20
        )
        self._attach_entity(self.boss)

        # 清除所有普通敌机（Boss 战期间不再刷怪）
        for enemy in self.enemies:
            self._detach_entity(enemy)
            self.pools.release(f'enemy_{enemy.enemy_type}', enemy)
        self.enemies.clear()

        # 播放Boss出场音效
        audio_manager.play_sfx('boss_appear')

    def trigger_shake(self, intensity: float = 8.0) -> None:
        """触发屏幕震动（取较强者，避免短间隔多次触发被弱化）。"""
        self.shake_intensity = max(self.shake_intensity, intensity)

    def _update_shake(self, dt: float) -> None:
        """更新屏幕震动：按 ``shake_decay`` 衰减并偏移根 widget。"""
        if self.shake_intensity < 0.3:
            self.shake_intensity = 0
            if self.root_widget:
                self.root_widget.pos = (0, 0)
            return
        self.shake_intensity *= self.shake_decay
        ox = random.uniform(-1, 1) * self.shake_intensity
        oy = random.uniform(-1, 1) * self.shake_intensity
        if self.root_widget:
            self.root_widget.pos = (int(ox), int(oy))

    def _update_combo(self, dt: float) -> None:
        """更新连击计时器：超时则清空连击。"""
        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

    def _on_kill(self) -> None:
        """击杀计数 + 连击累计。"""
        self.enemies_killed += 1
        self.combo += 1
        self.combo_timer = self.combo_timeout
        if self.combo > self.max_combo:
            self.max_combo = self.combo

    def _combo_bonus(self) -> int:
        """根据当前连击数返回分数倍率（1/2/3/5）。"""
        for threshold, multiplier in _COMBO_BONUS_TIERS:
            if self.combo >= threshold:
                return multiplier
        return 1

    def _clear_all_entities(self) -> None:
        """清空所有实体：卸载 widget、清空逻辑列表、归还对象池、清空粒子。"""
        # 卸载所有实体 widget（玩家由调用方单独处理）
        for entity in (
            *self.enemies,
            *self.bullets,
            *self.powerups,
            *self.explosions,
        ):
            self._detach_entity(entity)
        if self.boss:
            self._detach_entity(self.boss)

        self.player = None
        self.enemies.clear()
        self.bullets.clear()
        self.powerups.clear()
        self.explosions.clear()
        self.boss = None

        # 释放所有对象池
        self.pools.release_all()

        # 清空粒子
        particle_system.clear()

    def use_bomb(self) -> None:
        """使用炸弹：清屏敌机/敌方子弹、对Boss造成大量伤害、震屏。"""
        if not self.player or self.player.bombs <= 0:
            return

        self.player.use_bomb()

        # 清除所有敌机（直接加分 + 爆炸 + 归池）
        for enemy in self.enemies:
            self.score += enemy.score
            self._create_explosion(enemy.center, enemy.width)
            self._detach_entity(enemy)
            self.pools.release(f'enemy_{enemy.enemy_type}', enemy)
        self.enemies.clear()

        # 清除所有敌方子弹
        for bullet in self.bullets[:]:
            if not bullet.is_player:
                self._recycle_bullet(bullet)

        # 对Boss造成伤害
        if self.boss:
            self.boss.take_damage(10)
            if not self.boss.active:
                self.score += self.boss.score
                self._create_explosion(self.boss.center, self.boss.width * 1.5)
                self._detach_entity(self.boss)
                self.boss = None
                self.boss_spawned = False
                self.level += 1
                self.enemies_killed = 0

        # 震屏
        self.trigger_shake(12.0)

        # 播放音效
        audio_manager.play_sfx('bomb')

    def on_touch_down(self, touch) -> bool:
        """触摸按下：检测双击使用炸弹，否则记录拖拽偏移。"""
        if self.state != GameState.PLAYING or not self.player:
            return False

        current_time = time.time()

        # 检测双击（在 double_tap_threshold 时间窗口内再次按下）
        if current_time - self.last_tap_time < self.config.double_tap_threshold:
            self.use_bomb()
            self.last_tap_time = 0
            return True

        self.last_tap_time = current_time

        # 记录触摸位置与相对玩家位置的偏移，保证拖拽时手指与飞机的相对距离不变
        self.touch_pos = touch.pos
        self.touch_offset = (touch.x - self.player.x, touch.y - self.player.y)

        return True

    def on_touch_move(self, touch) -> bool:
        """触摸移动：更新触摸位置。"""
        if self.state != GameState.PLAYING or not self.player:
            return False

        self.touch_pos = touch.pos
        return True

    def on_touch_up(self, touch) -> bool:
        """触摸抬起：结束拖拽。"""
        self.touch_pos = None
        return False


# 全局游戏实例
game = Game()


def get_game() -> Game:
    """获取全局游戏实例"""
    return game
