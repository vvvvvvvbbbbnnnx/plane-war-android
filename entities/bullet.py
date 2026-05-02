"""
飞机大战 - 子弹
"""
from kivy.graphics import Color, Ellipse
from kivy.properties import BooleanProperty, NumericProperty

from config.settings import get_config
from core.entity import Entity
from utils.screen import screen


class Bullet(Entity):
    """
    子弹

    Attributes:
        is_player: 是否为玩家子弹
        damage: 伤害值
    """

    is_player = BooleanProperty(True)
    damage = NumericProperty(1)

    def __init__(self, is_player: bool = True, **kwargs):
        """
        初始化子弹

        Args:
            is_player: 是否为玩家子弹
        """
        self.is_player = is_player
        super().__init__(**kwargs)

        # 设置实体类型（用于碰撞检测）
        self.entity_type = 'bullet_player' if is_player else 'bullet_enemy'

        config = get_config()

        if is_player:
            # 玩家子弹
            self.set_size_rel(
                config.bullet.player_width_ratio,
                config.bullet.player_height_ratio
            )
            self._base_speed = config.bullet.player_speed
            self._color = (0.2, 1, 1)  # 青色
            self._image_file = 'bullet_player.png'
        else:
            # 敌方子弹
            self.set_size_rel(
                config.bullet.enemy_width_ratio,
                config.bullet.enemy_height_ratio
            )
            self._base_speed = config.bullet.enemy_speed
            self._color = (1, 0.3, 0.3)  # 红色
            self._image_file = 'bullet_enemy.png'

        # 设置速度
        self.speed = screen.scale_value(self._base_speed)

        # 尝试加载图片
        self._image_loaded = self.setup_image(self._image_file)

        # 碰撞盒
        self._hitbox_scale = 0.9

    def update(self, dt: float) -> None:
        """更新子弹"""
        super().update(dt)

        # 检查是否出界
        if self.is_player:
            if self.y > screen.real_height + self.height:
                self.active = False
        else:
            if self.y < -self.height:
                self.active = False

    def draw(self) -> None:
        """绘制子弹"""
        if self._image_loaded:
            return

        # 线条绘制模式
        self.canvas.clear()
        with self.canvas:
            Color(*self._color)
            Ellipse(pos=self.pos, size=self.size)

    def reset(self) -> None:
        """重置子弹状态"""
        super().reset()

        # 重新设置速度方向
        if self.is_player:
            self.velocity_y = self.speed
        else:
            self.velocity_y = -self.speed
