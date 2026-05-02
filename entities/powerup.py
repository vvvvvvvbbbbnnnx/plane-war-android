"""
飞机大战 - 道具
"""
import random

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import StringProperty

from config.settings import get_config
from core.entity import Entity
from utils.screen import screen


class PowerUp(Entity):
    """
    道具

    Attributes:
        powerup_type: 道具类型 ('health', 'weapon', 'shield', 'bomb')
    """

    powerup_type = StringProperty('health')

    # 道具颜色配置
    TYPE_COLORS: dict[str, tuple[float, float, float]] = {
        'health': (0.2, 1, 0.4),    # 绿色
        'weapon': (1, 1, 0.2),      # 黄色
        'shield': (0.2, 1, 1),      # 青色
        'bomb': (0.5, 0.5, 0.5),    # 灰色
    }

    # 道具图片映射
    TYPE_IMAGES: dict[str, str] = {
        'health': 'powerup_health.png',
        'weapon': 'powerup_weapon.png',
        'shield': 'powerup_shield.png',
        'bomb': 'powerup_bomb.png',
    }

    def __init__(self, powerup_type: str = 'health', **kwargs):
        """
        初始化道具

        Args:
            powerup_type: 道具类型
        """
        self._powerup_type = powerup_type
        super().__init__(**kwargs)

        # 设置实体类型（用于碰撞检测）
        self.entity_type = 'powerup'

        config = get_config()

        # 设置尺寸
        self.set_size_rel(config.powerup.width_ratio, config.powerup.height_ratio)

        # 设置速度
        self._base_speed = config.powerup.speed
        self.speed = screen.scale_value(self._base_speed)
        self.velocity_y = -self.speed

        # 获取颜色
        self._color = self.TYPE_COLORS.get(powerup_type, (1, 1, 1))

        # 尝试加载图片
        image_file = self.TYPE_IMAGES.get(powerup_type)
        if image_file:
            self._image_loaded = self.setup_image(image_file)
        else:
            self._image_loaded = False

        # 碰撞盒
        self._hitbox_scale = 0.8

    @property
    def powerup_type(self) -> str:  # noqa: F811
        return self._powerup_type

    def setup_type(self, powerup_type: str) -> None:
        """
        设置道具类型

        Args:
            powerup_type: 道具类型
        """
        self._powerup_type = powerup_type
        self._color = self.TYPE_COLORS.get(powerup_type, (1, 1, 1))

        # 尝试加载图片
        image_file = self.TYPE_IMAGES.get(powerup_type)
        if image_file:
            self._image_loaded = self.setup_image(image_file)

    def update(self, dt: float) -> None:
        """更新道具"""
        super().update(dt)

        # 检查是否出界
        if self.y < -self.height:
            self.active = False

    def draw(self) -> None:
        """绘制道具"""
        if self._image_loaded:
            return

        # 线条绘制模式
        self.canvas.clear()
        w, h = self.size

        with self.canvas:
            # 外圈
            Color(*self._color)
            Ellipse(pos=self.pos, size=self.size)

            # 根据类型绘制不同图标
            if self.powerup_type == 'health':
                # 十字
                Color(1, 1, 1)
                cross_w = w * 0.15
                cross_h = h * 0.6
                Rectangle(
                    pos=(self.center_x - cross_w/2, self.y + h*0.2),
                    size=(cross_w, cross_h)
                )
                Rectangle(
                    pos=(self.x + w*0.2, self.center_y - cross_w/2),
                    size=(cross_h, cross_w)
                )

            elif self.powerup_type == 'weapon':
                # 闪电
                Color(1, 0.84, 0)
                points = [
                    (self.center_x + w*0.1, self.top - h*0.1),
                    (self.x + w*0.25, self.center_y),
                    (self.center_x, self.center_y),
                    (self.center_x - w*0.1, self.y + h*0.1),
                    (self.right - w*0.25, self.center_y),
                    (self.center_x, self.center_y),
                ]
                Line(points=points, width=screen.dp(2))

            elif self.powerup_type == 'shield':
                # 盾牌
                Color(1, 1, 1, 0.8)
                shield_points = [
                    (self.center_x, self.top - h*0.1),
                    (self.x + w*0.15, self.y + h*0.3),
                    (self.center_x, self.y + h*0.1),
                    (self.right - w*0.15, self.y + h*0.3),
                ]
                Line(points=shield_points, width=screen.dp(2), close=True)

            elif self.powerup_type == 'bomb':
                # 炸弹
                Color(0.2, 0.2, 0.2)
                Ellipse(
                    pos=(self.x + w*0.2, self.y + h*0.2),
                    size=(w * 0.6, h * 0.6)
                )
                Color(1, 0.5, 0)
                # 引信
                Line(
                    points=[
                        (self.center_x, self.top - h*0.2),
                        (self.center_x + w*0.15, self.top),
                    ],
                    width=screen.dp(2)
                )

    def apply(self, player) -> None:
        """应用道具效果到玩家"""
        if self.powerup_type == 'health':
            player.heal(1)
        elif self.powerup_type == 'weapon':
            player.upgrade_weapon()
        elif self.powerup_type == 'shield':
            player.activate_shield()
        elif self.powerup_type == 'bomb':
            player.add_bomb(1)

    def reset(self) -> None:
        super().reset()
        self.velocity_y = -self.speed

    @classmethod
    def get_random_type(cls) -> str:
        """
        获取随机道具类型

        Returns:
            随机道具类型
        """
        config = get_config()
        return random.choice(config.powerup.types)
