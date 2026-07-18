"""
飞机大战 - Boss (多阶段攻击模式)

设计要点
--------
* 双阶段：血量 > 50% 为阶段 1（左右巡逻 + 3 发齐射）；
  血量 ≤ 50% 进入阶段 2（暴怒模式，移速提升 + 周期性朝玩家冲刺 + 5 发扇形散射）。
* 玩家引用通过 ``_get_player`` 延迟导入 ``core.game`` 获取，避免反向穿透 widget 树。
* 出场前 1 秒从顶部滑入，期间不攻击。
"""
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.properties import NumericProperty

from config.settings import get_config
from core.entity import Entity
from utils.screen import screen


class Boss(Entity):
    level = NumericProperty(1)
    health = NumericProperty(20)
    max_health = NumericProperty(20)
    score = NumericProperty(1000)

    def __init__(self, level: int = 1, **kwargs):
        self._level = level
        super().__init__(**kwargs)
        self.entity_type = 'boss'
        config = get_config()
        # 体型随等级增长，但封顶以避免占满屏幕
        base_w = min(config.boss.width_ratio + level * 0.02, 0.4)
        base_h = min(config.boss.height_ratio + level * 0.01, 0.15)
        self.set_size_rel(base_w, base_h)
        self.health = config.boss.base_health + level * config.boss.health_per_level
        self.max_health = self.health
        self.score = config.boss.base_score * level
        self._base_speed = config.boss.speed
        self.speed = screen.scale_value(self._base_speed)
        self.direction = 1
        self._shoot_interval = config.boss.shoot_interval
        self._shoot_timer = 0

        # 多阶段状态
        self._charge_timer = 0.0
        self._charge_cooldown = 3.0
        self._flash_timer = 0.0
        self._rage_mode = False

        self._image_loaded = self.setup_image('boss.png')
        self._hitbox_scale = 0.85
        self._move_timer = 0.0

    @property
    def is_phase2(self) -> bool:  # noqa: F811
        """是否进入暴怒阶段（血量 ≤ 50%）。"""
        return self.get_health_ratio() <= 0.5

    def _get_player(self):
        """获取玩家引用（延迟导入 game 单例，避免与 core.game 循环导入）。"""
        from core.game import get_game
        return get_game().player

    def update(self, dt: float) -> None:
        """更新Boss：出场滑入 → 阶段 1/2 行为。"""
        super().update(dt)
        if self._flash_timer > 0:
            self._flash_timer -= dt
        self._charge_timer += dt
        self._shoot_timer += dt

        # 出场动画：前 1 秒从顶部滑入目标位置，期间不攻击
        if self._move_timer < 1.0:
            self._move_timer += dt
            target_y = screen.real_height - self.height - 20
            self.y += (target_y - self.y) * 0.05
            if self._move_timer >= 1.0:
                self.y = target_y
            return

        if self.is_phase2:
            self._update_phase2(dt)
        else:
            self._update_phase1(dt)

    def _update_phase1(self, dt: float) -> None:
        """阶段 1：左右巡逻 + 3 发齐射。"""
        self.x += self.speed * self.direction * dt * 60
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x >= screen.real_width - self.width:
            self.x = screen.real_width - self.width
            self.direction = -1

    def _update_phase2(self, dt: float) -> None:
        """阶段 2：暴怒模式 — 更快的移动 + 周期性朝玩家冲刺。"""
        if not self._rage_mode:
            self._shoot_interval = 0.3  # 射击更快
            self.speed *= 1.6
            self._rage_mode = True

        # 周期性冲刺：朝玩家横向位置冲刺并下压
        if self._charge_timer > self._charge_cooldown:
            self._charge_timer = 0
            player = self._get_player()
            if player:
                target_x = player.center_x
                self.velocity_x = (target_x - self.center_x) * 3
                self.velocity_y = -self.speed * 3

        self.x += self.velocity_x * dt * 60
        self.y += self.velocity_y * dt * 60
        # 减速回到正常
        self.velocity_x *= 0.95
        self.velocity_y *= 0.95
        # 边界钳制
        self.x = max(0, min(screen.real_width - self.width, self.x))
        self.y = max(screen.real_height * 0.3, min(screen.real_height - self.height, self.y))

    def should_shoot(self) -> bool:
        """射击间隔达标则开火（重置计时器）。"""
        if self._shoot_timer >= self._shoot_interval:
            self._shoot_timer = 0
            return True
        return False

    def get_shoot_positions(self) -> list:
        """返回本帧发射点列表：阶段 1 为 3 发并排，阶段 2 为 5 发扇形散射。"""
        if self.is_phase2:
            # 5 发扇形散射
            positions = []
            for i in range(5):
                x = self.x + self.width * (0.05 + i * 0.225)
                y = self.y
                positions.append((x, y))
            return positions
        # 3 发并排
        positions = []
        for i in range(3):
            x = self.x + self.width * (0.15 + i * 0.35)
            y = self.y
            positions.append((x, y))
        return positions

    def take_damage(self, amount: int = 1) -> bool:
        """承受伤害并触发短暂闪白；血量归零则标记失活。"""
        self.health -= amount
        self._flash_timer = 0.08
        if self.health <= 0:
            self.active = False
            return True
        return False

    def get_health_ratio(self) -> float:
        """返回当前血量比例（0~1）。"""
        return max(0, self.health / self.max_health)

    def draw(self) -> None:
        """绘制Boss：贴图模式叠加闪白与血条；无贴图时用椭圆矢量绘制。"""
        flash = self._flash_timer > 0
        if self._image_loaded:
            if flash:
                self.canvas.after.clear()
                with self.canvas.after:
                    Color(1, 1, 1, 0.4)
                    Rectangle(pos=self.pos, size=self.size)
            self._draw_health_bar()
            return
        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            Color(1, 0.5, 0.5) if flash else Color(0.5, 0, 0)
            Ellipse(pos=self.pos, size=self.size)
            Color(1, 0.7, 0.7) if flash else Color(0.8, 0.2, 0.2)
            Ellipse(pos=(self.x + w*0.08, self.y + h*0.06), size=(w*0.84, h*0.88))
            # 核心：阶段 2 变为黄色闪烁
            core_c = (1, 1, 0.5) if self.is_phase2 else (1, 0.84, 0)
            Color(*core_c)
            cs = min(w, h) * 0.3
            Ellipse(pos=(self.center_x - cs/2, self.center_y - cs/2), size=(cs, cs))
        self._draw_health_bar()

    def _draw_health_bar(self) -> None:
        """在Boss上方绘制血条（阶段 2 变色提示）。"""
        self.canvas.after.clear()
        with self.canvas.after:
            bh = screen.dp(8)
            by_ = self.top + screen.dp(5)
            Color(0.3, 0.3, 0.3)
            Rectangle(pos=(self.x, by_), size=(self.width, bh))
            Color(1, 0.3, 0.1) if self.is_phase2 else Color(1, 0, 0)
            Rectangle(pos=(self.x, by_), size=(self.width * self.get_health_ratio(), bh))

    def reset(self) -> None:
        """重置Boss状态（对象池复用时调用）。"""
        super().reset()
        self._shoot_timer = 0
        self._charge_timer = 0.0
        self._flash_timer = 0.0
        self._rage_mode = False
        self._move_timer = 0.0
        self.direction = 1
