"""
飞机大战 - Boss
"""
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.properties import NumericProperty

from config.settings import get_config
from core.entity import Entity
from utils.screen import screen


class Boss(Entity):
    """
    Boss敌机

    Attributes:
        level: Boss等级
        health: 当前生命值
        max_health: 最大生命值
        score: 击杀得分
        direction: 移动方向 (1 或 -1)
    """

    level = NumericProperty(1)
    health = NumericProperty(20)
    max_health = NumericProperty(20)
    score = NumericProperty(1000)

    def __init__(self, level: int = 1, **kwargs):
        """
        初始化Boss

        Args:
            level: Boss等级
        """
        self._level = level
        super().__init__(**kwargs)

        self.entity_type = 'boss'
        config = get_config()

        # Boss尺寸随等级增加
        base_w = config.boss.width_ratio + level * 0.02
        base_h = config.boss.height_ratio + level * 0.01
        self.set_size_rel(min(base_w, 0.4), min(base_h, 0.15))

        # 生命值
        self.health = config.boss.base_health + level * config.boss.health_per_level
        self.max_health = self.health
        self.score = config.boss.base_score * level

        # 移动
        self._base_speed = config.boss.speed
        self.speed = screen.scale_value(self._base_speed)
        self.direction = 1  # 1: 右, -1: 左

        # 射击
        self._shoot_interval = config.boss.shoot_interval
        self._shoot_timer = 0

        # 尝试加载图片
        self._image_loaded = self.setup_image('boss.png')

        # 碰撞盒
        self._hitbox_scale = 0.9

    def update(self, dt: float) -> None:
        super().update(dt)
        self.x += self.speed * self.direction * dt * 60
        if self.x <= 0:
            self.x = 0
            self.direction = 1
        elif self.x >= screen.real_width - self.width:
            self.x = screen.real_width - self.width
            self.direction = -1
        self._shoot_timer += dt

    def should_shoot(self) -> bool:
        """
        检查是否应该射击

        Returns:
            是否射击
        """
        if self._shoot_timer >= self._shoot_interval:
            self._shoot_timer = 0
            return True
        return False

    def get_shoot_positions(self) -> list:
        """
        获取射击位置

        Returns:
            [(x1, y1), (x2, y2), ...] 射击位置列表
        """
        positions = []
        for i in range(3):
            x = self.x + self.width * (0.15 + i * 0.35)
            y = self.y
            positions.append((x, y))
        return positions

    def take_damage(self, amount: int = 1) -> bool:
        self.health -= amount
        if self.health <= 0:
            self.active = False
            return True
        return False

    def get_health_ratio(self) -> float:
        """
        获取生命值比例

        Returns:
            生命值比例 (0-1)
        """
        return self.health / self.max_health

    def draw(self) -> None:
        """绘制Boss"""
        if self._image_loaded:
            self._draw_health_bar()
            return

        # 线条绘制模式
        self.canvas.clear()
        w, h = self.size

        with self.canvas:
            # 主体
            Color(0.5, 0, 0)
            Ellipse(pos=self.pos, size=self.size)

            Color(0.8, 0.2, 0.2)
            Ellipse(
                pos=(self.x + w*0.08, self.y + h*0.06),
                size=(w * 0.84, h * 0.88)
            )

            # 核心
            Color(1, 0.84, 0)
            core_size = min(w, h) * 0.3
            Ellipse(
                pos=(self.center_x - core_size/2, self.center_y - core_size/2),
                size=(core_size, core_size)
            )

        # 绘制血条
        self._draw_health_bar()

    def _draw_health_bar(self) -> None:
        """绘制血条"""
        self.canvas.after.clear()

        with self.canvas.after:
            bar_height = screen.dp(8)
            bar_y = self.top + screen.dp(5)

            # 背景
            Color(0.3, 0.3, 0.3)
            Rectangle(
                pos=(self.x, bar_y),
                size=(self.width, bar_height)
            )

            # 血量
            Color(1, 0, 0)
            health_ratio = self.get_health_ratio()
            Rectangle(
                pos=(self.x, bar_y),
                size=(self.width * health_ratio, bar_height)
            )

    def reset(self) -> None:
        """重置Boss状态"""
        super().reset()
        self._shoot_timer = 0
        self.direction = 1
