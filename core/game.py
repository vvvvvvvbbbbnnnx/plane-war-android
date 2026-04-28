# -*- coding: utf-8 -*-
"""
飞机大战 - 游戏主循环

整合所有模块，管理游戏状态和场景切换
"""
import random
from typing import Optional, Dict, Any, List
from enum import Enum
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.core.window import Window

from config.settings import get_config
from core.pool import MultiTypePool
from entities.player import Player
from entities.enemy import Enemy
from entities.boss import Boss
from entities.bullet import Bullet
from entities.powerup import PowerUp
from entities.explosion import Explosion
from systems.collision import CollisionSystem
from systems.audio import audio_manager
from systems.particle import particle_system
from systems.save import save_manager
from systems.achievement import achievement_manager
from utils.screen import screen, update_screen
from utils.helpers import chance, random_int


class GameState(Enum):
    """游戏状态枚举"""
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    GAME_OVER = 'game_over'


class Game:
    """
    游戏主类（单例模式）

    管理游戏状态、场景切换、实体生命周期
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

        # 实体
        self.player: Optional[Player] = None
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.powerups: List[PowerUp] = []
        self.explosions: List[Explosion] = []
        self.boss: Optional[Boss] = None

        # 对象池
        self.pools = MultiTypePool()
        self._setup_pools()

        # 碰撞系统
        self.collision = CollisionSystem()
        self._setup_collision_groups()

        # 计时器
        self.spawn_timer = 0.0
        self.shoot_timer = 0.0

        # 触摸控制
        self.touch_pos = None
        self.touch_offset = (0, 0)
        self.last_tap_time = 0.0

        # UI组件（由外部设置）
        self.ui_container: Optional[FloatLayout] = None

        # 绑定窗口大小变化
        Window.bind(on_resize=self._on_window_resize)

    def _setup_pools(self) -> None:
        """设置对象池"""
        # 子弹池
        self.pools.register(
            'bullet_player',
            lambda: Bullet(is_player=True),
            initial_size=100
        )
        self.pools.register(
            'bullet_enemy',
            lambda: Bullet(is_player=False),
            initial_size=50
        )

        # 敌机池
        self.pools.register(
            'enemy_normal',
            lambda: Enemy(enemy_type='normal'),
            initial_size=20
        )
        self.pools.register(
            'enemy_fast',
            lambda: Enemy(enemy_type='fast'),
            initial_size=10
        )
        self.pools.register(
            'enemy_tank',
            lambda: Enemy(enemy_type='tank'),
            initial_size=10
        )

        # 道具池
        self.pools.register(
            'powerup',
            lambda: PowerUp(),
            initial_size=10
        )

    def _setup_collision_groups(self) -> None:
        """设置碰撞组"""
        # 玩家子弹 vs 敌机
        self.collision.register_collision_group(
            'bullet_player', 'enemy',
            self._on_bullet_hit_enemy
        )

        # 玩家子弹 vs Boss
        self.collision.register_collision_group(
            'bullet_player', 'boss',
            self._on_bullet_hit_boss
        )

        # 敌方子弹 vs 玩家
        self.collision.register_collision_group(
            'bullet_enemy', 'player',
            self._on_bullet_hit_player
        )

        # 道具 vs 玩家
        self.collision.register_collision_group(
            'powerup', 'player',
            self._on_powerup_collected
        )

    def _on_window_resize(self, instance, width, height) -> None:
        """窗口大小变化处理"""
        update_screen()

    def start_game(self) -> None:
        """开始新游戏"""
        # 重置状态
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.enemies_killed = 0
        self.boss_spawned = False

        # 清空实体
        self._clear_all_entities()

        # 创建玩家
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
        """游戏结束"""
        self.state = GameState.GAME_OVER

        # 保存分数
        save_manager.save_high_score(self.score)

        # 更新统计
        save_manager.update_statistics({
            'total_games': 1,
            'total_score': self.score,
            'max_level_reached': max(save_manager.load_statistics().get('max_level_reached', 0), self.level),
        })

        # 停止音乐
        audio_manager.stop_music()

    def update(self, dt: float) -> None:
        """
        游戏主更新循环

        Args:
            dt: 时间增量
        """
        if self.state != GameState.PLAYING:
            return

        # 更新计时器
        self.spawn_timer += dt
        self.shoot_timer += dt

        # 获取关卡配置
        level_config = self.config.get_level(self.level)

        # 生成敌机
        if self.spawn_timer >= level_config.spawn_rate and not self.boss_spawned:
            self.spawn_timer = 0
            self._spawn_enemy(level_config.enemy_types)

        # 自动射击
        if self.shoot_timer >= self.config.shoot_cooldown:
            self.shoot_timer = 0
            self._player_shoot()

        # 更新玩家
        self._update_player(dt)

        # 更新敌机
        self._update_enemies(dt)

        # 更新子弹
        self._update_bullets(dt)

        # 更新道具
        self._update_powerups(dt)

        # 更新爆炸
        self._update_explosions(dt)

        # 更新Boss
        if self.boss:
            self._update_boss(dt)

        # 更新粒子
        particle_system.update(dt)

        # 碰撞检测
        self._check_collisions()

        # 检查关卡进度
        self._check_level_progress(level_config)

    def _spawn_enemy(self, enemy_types: List[str]) -> None:
        """生成敌机"""
        enemy_type = random.choice(enemy_types)
        pool_name = f'enemy_{enemy_type}'

        enemy = self.pools.acquire(pool_name)
        enemy.pos = (
            random_int(20, int(screen.real_width - enemy.width - 20)),
            screen.real_height
        )

        self.enemies.append(enemy)

    def _player_shoot(self) -> None:
        """玩家射击"""
        if not self.player:
            return

        offsets = {1: [0], 2: [-0.02, 0.02], 3: [-0.03, 0, 0.03]}
        weapon_level = min(self.player.weapon_level, 3)

        for offset in offsets.get(weapon_level, [0]):
            bullet = self.pools.acquire('bullet_player')
            bullet.pos = (
                self.player.center_x - bullet.width / 2 + screen.rel_w(offset),
                self.player.top
            )
            self.bullets.append(bullet)

        # 播放射击音效
        audio_manager.play_sfx('shoot')

    def _update_player(self, dt: float) -> None:
        """更新玩家"""
        if not self.player:
            return

        # 触摸移动
        if self.touch_pos:
            target_x = self.touch_pos[0] - self.touch_offset[0]
            target_y = self.touch_pos[1] - self.touch_offset[1]
            self.player.move_to(target_x, target_y, smooth=True)

        self.player.update(dt)

    def _update_enemies(self, dt: float) -> None:
        """更新敌机"""
        for enemy in self.enemies[:]:
            enemy.update(dt)

            # 敌机射击
            if enemy.should_shoot():
                bullet = self.pools.acquire('bullet_enemy')
                bullet.pos = (enemy.center_x - bullet.width / 2, enemy.y)
                self.bullets.append(bullet)

            # 移除出界敌机
            if not enemy.is_on_screen(margin=enemy.height):
                self.enemies.remove(enemy)
                self.pools.release(f'enemy_{enemy.enemy_type}', enemy)

    def _update_bullets(self, dt: float) -> None:
        """更新子弹"""
        for bullet in self.bullets[:]:
            bullet.update(dt)

            # 移除出界子弹
            if not bullet.is_on_screen():
                self.bullets.remove(bullet)
                pool_name = 'bullet_player' if bullet.is_player else 'bullet_enemy'
                self.pools.release(pool_name, bullet)

    def _update_powerups(self, dt: float) -> None:
        """更新道具"""
        for powerup in self.powerups[:]:
            powerup.update(dt)

            if not powerup.is_on_screen():
                self.powerups.remove(powerup)
                self.pools.release('powerup', powerup)

    def _update_explosions(self, dt: float) -> None:
        """更新爆炸"""
        for explosion in self.explosions[:]:
            explosion.update(dt)
            if not explosion.active:
                self.explosions.remove(explosion)

    def _update_boss(self, dt: float) -> None:
        """更新Boss"""
        if not self.boss:
            return

        self.boss.update(dt)

        # Boss射击
        if self.boss.should_shoot():
            for pos in self.boss.get_shoot_positions():
                bullet = self.pools.acquire('bullet_enemy')
                bullet.pos = pos
                self.bullets.append(bullet)

    def _check_collisions(self) -> None:
        """检测碰撞"""
        # 收集所有活动实体
        entities = []
        if self.player:
            entities.append(self.player)
        entities.extend(self.enemies)
        entities.extend(self.bullets)
        entities.extend(self.powerups)
        if self.boss:
            entities.append(self.boss)

        # 更新碰撞系统
        self.collision.update(entities)
        self.collision.check_collisions()

    def _on_bullet_hit_enemy(self, bullet: Bullet, enemy: Enemy) -> None:
        """子弹击中敌机"""
        enemy.take_damage(bullet.damage)

        # 移除子弹
        if bullet in self.bullets:
            self.bullets.remove(bullet)
            self.pools.release('bullet_player', bullet)

        if not enemy.active:
            # 敌机死亡
            self.score += enemy.score
            self.enemies_killed += 1

            # 创建爆炸
            self._create_explosion(enemy.center, enemy.width)

            # 移除敌机
            if enemy in self.enemies:
                self.enemies.remove(enemy)
                self.pools.release(f'enemy_{enemy.enemy_type}', enemy)

            # 掉落道具
            if chance(self.config.powerup.drop_rate):
                self._spawn_powerup(enemy.center)

            # 播放音效
            audio_manager.play_sfx('explosion')

            # 成就检查
            achievement_manager.increment_achievement('first_blood')
            achievement_manager.increment_achievement('killer_10')
            achievement_manager.increment_achievement('killer_100')
            achievement_manager.increment_achievement('killer_1000')

    def _on_bullet_hit_boss(self, bullet: Bullet, boss: Boss) -> None:
        """子弹击中Boss"""
        boss.take_damage(bullet.damage)

        # 移除子弹
        if bullet in self.bullets:
            self.bullets.remove(bullet)
            self.pools.release('bullet_player', bullet)

        if not boss.active:
            # Boss死亡
            self.score += boss.score

            # 创建大爆炸
            self._create_explosion(boss.center, boss.width * 1.5)

            # 移除Boss
            self.boss = None
            self.boss_spawned = False

            # 进入下一关
            self.level += 1
            self.enemies_killed = 0

            # 播放音效
            audio_manager.play_sfx('boss_death')

            # 成就检查
            achievement_manager.increment_achievement('boss_first')
            achievement_manager.increment_achievement('boss_5')
            achievement_manager.increment_achievement('boss_10')

    def _on_bullet_hit_player(self, bullet: Bullet, player: Player) -> None:
        """子弹击中玩家"""
        if player.shield or player.invincible:
            return

        # 移除子弹
        if bullet in self.bullets:
            self.bullets.remove(bullet)
            self.pools.release('bullet_enemy', bullet)

        # 玩家受伤
        player.take_damage()

        # 播放音效
        audio_manager.play_sfx('hit')

        if player.health <= 0:
            player.lives -= 1
            if player.lives <= 0:
                self.game_over()
            else:
                # 复活
                player.health = player.max_health
                player.invincible = True
                player.invincible_time = self.config.player.invincible_time

    def _on_powerup_collected(self, powerup: PowerUp, player: Player) -> None:
        """收集道具"""
        powerup.apply(player)

        # 移除道具
        if powerup in self.powerups:
            self.powerups.remove(powerup)
            self.pools.release('powerup', powerup)

        # 播放音效
        audio_manager.play_sfx('powerup')

    def _spawn_powerup(self, pos: tuple) -> None:
        """生成道具"""
        powerup = self.pools.acquire('powerup')
        powerup_type = random.choice(self.config.powerup.types)
        powerup.setup_type(powerup_type)
        powerup.pos = (pos[0] - powerup.width / 2, pos[1] - powerup.height / 2)
        self.powerups.append(powerup)

    def _create_explosion(self, pos: tuple, size: float) -> None:
        """创建爆炸效果"""
        explosion = Explosion(pos=pos, size_ratio=size / screen.real_width)
        self.explosions.append(explosion)

        # 粒子效果
        particle_system.emit(pos[0], pos[1], 'explosion', count=15)

    def _check_level_progress(self, level_config) -> None:
        """检查关卡进度"""
        if self.enemies_killed >= level_config.enemies_to_kill and not self.boss_spawned:
            self._spawn_boss()

    def _spawn_boss(self) -> None:
        """生成Boss"""
        self.boss_spawned = True
        self.boss = Boss(level=self.level)
        self.boss.pos = (
            screen.real_width / 2 - self.boss.width / 2,
            screen.real_height - self.boss.height - 20
        )

        # 清除所有敌机
        for enemy in self.enemies:
            self.pools.release(f'enemy_{enemy.enemy_type}', enemy)
        self.enemies.clear()

        # 播放Boss音效
        audio_manager.play_sfx('boss_appear')

    def _clear_all_entities(self) -> None:
        """清空所有实体"""
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
        """使用炸弹"""
        if not self.player or self.player.bombs <= 0:
            return

        self.player.use_bomb()

        # 清除所有敌机
        for enemy in self.enemies:
            self.score += enemy.score
            self._create_explosion(enemy.center, enemy.width)
            self.pools.release(f'enemy_{enemy.enemy_type}', enemy)
        self.enemies.clear()

        # 清除敌方子弹
        for bullet in self.bullets[:]:
            if not bullet.is_player:
                self.bullets.remove(bullet)
                self.pools.release('bullet_enemy', bullet)

        # 对Boss造成伤害
        if self.boss:
            self.boss.take_damage(10)
            if not self.boss.active:
                self.score += self.boss.score
                self._create_explosion(self.boss.center, self.boss.width * 1.5)
                self.boss = None
                self.boss_spawned = False
                self.level += 1
                self.enemies_killed = 0

        # 播放音效
        audio_manager.play_sfx('bomb')

    def on_touch_down(self, touch) -> bool:
        """触摸按下"""
        if self.state != GameState.PLAYING or not self.player:
            return False

        import time
        current_time = time.time()

        # 检测双击
        if current_time - self.last_tap_time < self.config.double_tap_threshold:
            self.use_bomb()
            self.last_tap_time = 0
            return True

        self.last_tap_time = current_time

        # 记录触摸位置
        self.touch_pos = touch.pos
        self.touch_offset = (touch.x - self.player.x, touch.y - self.player.y)

        return True

    def on_touch_move(self, touch) -> bool:
        """触摸移动"""
        if self.state != GameState.PLAYING or not self.player:
            return False

        self.touch_pos = touch.pos
        return True

    def on_touch_up(self, touch) -> bool:
        """触摸抬起"""
        self.touch_pos = None
        return False


# 全局游戏实例
game = Game()


def get_game() -> Game:
    """获取全局游戏实例"""
    return game
