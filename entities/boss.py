"""
飞机大战 - Boss (多阶段攻击模式)
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
        self._spawn_pos = None  # 出场动画用

        self._image_loaded = self.setup_image('boss.png')
        self._hitbox_scale = 0.85
        self._move_timer = 0.0

    @property
    def is_phase2(self) -> bool:  # noqa: F811
        return self.get_health_ratio() <= 0.5

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._flash_timer > 0:
            self._flash_timer -= dt
        self._charge_timer += dt
        self._shoot_timer += dt

        # 出场动画：前 1 秒不攻击，从顶部滑入
        if self._move_timer < 1.0:
            self._move_timer = getattr(self, '_move_timer', 0) + dt
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
        """阶段 1：左右巡逻 + 3 发齐射"""
        self.x += self.speed * self.direction * dt * 60
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x >= screen.real_width - self.width:
            self.x = screen.real_width - self.width
            self.direction = -1

    def _update_phase2(self, dt: float) -> None:
        """阶段 2：暴怒模式 — 更快的移动 + 偶尔冲刺"""
        if not self._rage_mode:
            self._shoot_interval = 0.3  # 射击更快
            self.speed *= 1.6
            self._rage_mode = True

        # 周期性冲刺
        if self._charge_timer > self._charge_cooldown:
            self._charge_timer = 0
            # 朝玩家位置冲刺
            if self.parent:
                game_root = self.parent
                player_holder = getattr(game_root, 'game', None)
                if player_holder and player_holder.player:
                    target_x = player_holder.player.center_x
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
        if self._shoot_timer >= self._shoot_interval:
            self._shoot_timer = 0
            return True
        return False

    def get_shoot_positions(self) -> list:
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
        self.health -= amount
        self._flash_timer = 0.08
        if self.health <= 0:
            self.active = False
            return True
        return False

    def get_health_ratio(self) -> float:
        return max(0, self.health / self.max_health)

    def draw(self) -> None:
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
            core_c = (1, 1, 0.5) if self.is_phase2 else (1, 0.84, 0)
            Color(*core_c)
            cs = min(w, h) * 0.3
            Ellipse(pos=(self.center_x - cs/2, self.center_y - cs/2), size=(cs, cs))
        self._draw_health_bar()

    def _draw_health_bar(self) -> None:
        self.canvas.after.clear()
        with self.canvas.after:
            bh = screen.dp(8)
            by_ = self.top + screen.dp(5)
            Color(0.3, 0.3, 0.3)
            Rectangle(pos=(self.x, by_), size=(self.width, bh))
            Color(1, 0.3, 0.1) if self.is_phase2 else Color(1, 0, 0)
            Rectangle(pos=(self.x, by_), size=(self.width * self.get_health_ratio(), bh))

    def reset(self) -> None:
        super().reset()
        self._shoot_timer = 0
        self._charge_timer = 0.0
        self._flash_timer = 0.0
        self._rage_mode = False
        self._move_timer = 0.0
        self.direction = 1
