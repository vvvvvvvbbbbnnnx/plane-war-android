"""
飞机大战 - 玩家飞机
"""
import time

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import BooleanProperty, NumericProperty

from config.settings import get_config
from core.entity import Entity
from utils.screen import screen


class Player(Entity):
    """
    玩家飞机

    Attributes:
        health: 当前生命值
        max_health: 最大生命值
        weapon_level: 武器等级 (1-3)
        shield: 是否有护盾
        shield_time: 护盾剩余时间
        invincible: 是否无敌
        invincible_time: 无敌剩余时间
        bombs: 炸弹数量
    """

    # 生命和武器
    health = NumericProperty(3)
    max_health = NumericProperty(3)
    weapon_level = NumericProperty(1)

    # 状态
    shield = BooleanProperty(False)
    invincible = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entity_type = 'player'

        # 加载配置
        config = get_config()
        self.max_health = config.player.max_health
        self.health = self.max_health
        self.max_weapon_level = config.player.max_weapon_level
        self._base_speed = config.player.base_speed
        self._invincible_time = config.player.invincible_time
        self._shield_duration = config.player.shield_duration
        self.max_bombs = config.player.max_bombs
        self.max_lives = config.player.max_lives

        # 当前状态
        self.weapon_level = 1
        self.shield = False
        self.shield_time = 0.0
        self.invincible = False
        self.invincible_time = 0.0
        self.bombs = 3
        self.lives = 3

        # 移动速度
        self.speed = screen.scale_value(self._base_speed)

        # 设置尺寸
        self.set_size_rel(0.12, 0.08)

        # 尝试加载图片
        self._image_loaded = self.setup_image('player.png')

        # 碰撞盒设置（稍小于实际尺寸）
        self._hitbox_scale = 0.7

    def update(self, dt: float) -> None:
        """更新玩家状态"""
        super().update(dt)

        # 更新护盾
        if self.shield:
            self.shield_time -= dt
            if self.shield_time <= 0:
                self.shield = False
                self.shield_time = 0

        # 更新无敌
        if self.invincible:
            self.invincible_time -= dt
            if self.invincible_time <= 0:
                self.invincible = False
                self.invincible_time = 0

    def move_to(self, target_x: float, target_y: float, smooth: bool = True) -> None:
        """
        移动到目标位置

        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            smooth: 是否平滑移动
        """
        if smooth:
            # 平滑移动 - 使用插值
            dx = target_x - self.x
            dy = target_y - self.y

            # 使用更平滑的移动方式
            lerp_factor = 0.3  # 插值因子，越大移动越快

            self.x += dx * lerp_factor
            self.y += dy * lerp_factor
        else:
            self.x = target_x
            self.y = target_y

        # 边界限制
        self.x = max(0, min(screen.real_width - self.width, self.x))
        self.y = max(0, min(screen.real_height - self.height, self.y))

    def take_damage(self) -> bool:
        """
        受到伤害

        内部处理「血量归零 → 扣命 → 复活回血」流程：
        * 受护盾/无敌保护时直接返回 False（不受伤）。
        * 受伤扣 1 血并降一级武器，触发短暂无敌。
        * 血量归零时扣 1 命；仍有剩余生命则回满血并延长无敌时间。
        * 生命耗尽（lives <= 0）时不再复活，返回 True 表示真正死亡。

        Returns:
            是否真正死亡（生命耗尽）
        """
        if self.shield or self.invincible:
            return False

        self.health -= 1
        self.weapon_level = max(1, self.weapon_level - 1)

        # 触发无敌
        self.invincible = True
        self.invincible_time = self._invincible_time

        if self.health <= 0:
            self.lives -= 1
            if self.lives > 0:
                # 复活：回满血并给予双倍无敌时间
                self.health = self.max_health
                self.invincible = True
                self.invincible_time = self._invincible_time * 2
            return self.lives <= 0

        return False

    def activate_shield(self, duration: float = None) -> None:
        """
        激活护盾

        Args:
            duration: 持续时间，None使用默认值
        """
        self.shield = True
        self.shield_time = duration if duration else self._shield_duration

    def upgrade_weapon(self) -> bool:
        """
        升级武器

        Returns:
            是否升级成功
        """
        if self.weapon_level < self.max_weapon_level:
            self.weapon_level += 1
            return True
        return False

    def add_bomb(self, count: int = 1) -> bool:
        """
        添加炸弹

        Args:
            count: 数量

        Returns:
            是否添加成功
        """
        if self.bombs < self.max_bombs:
            self.bombs = min(self.max_bombs, self.bombs + count)
            return True
        return False

    def use_bomb(self) -> bool:
        """
        使用炸弹

        Returns:
            是否使用成功
        """
        if self.bombs > 0:
            self.bombs -= 1
            return True
        return False

    def heal(self, amount: int = 1) -> bool:
        """
        恢复生命

        Args:
            amount: 恢复量

        Returns:
            是否恢复成功
        """
        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + amount)
            return True
        return False

    def add_life(self) -> bool:
        """
        增加生命

        Returns:
            是否增加成功
        """
        if self.lives < self.max_lives:
            self.lives += 1
            return True
        return False

    def draw(self) -> None:
        """绘制玩家"""
        if self._image_loaded:
            # 图片模式下只绘制效果
            self._draw_effects()
            return

        # 线条绘制模式
        self.canvas.clear()
        with self.canvas:
            w, h = self.size

            # 主体
            Color(0.2, 1, 1, 1)
            body_points = [
                (self.center_x, self.top),
                (self.x + w * 0.17, self.y + h * 0.25),
                (self.x + w * 0.08, self.y),
                (self.right - w * 0.08, self.y),
                (self.right - w * 0.17, self.y + h * 0.25),
            ]
            Line(points=body_points, width=screen.dp(2), close=True)

            # 机翼
            Color(0.2, 0.6, 1, 1)
            left_wing = [
                (self.x + w * 0.17, self.y + h * 0.375),
                (self.x, self.y + h * 0.125),
                (self.x + w * 0.25, self.y + h * 0.25),
            ]
            right_wing = [
                (self.right - w * 0.17, self.y + h * 0.375),
                (self.right, self.y + h * 0.125),
                (self.right - w * 0.25, self.y + h * 0.25),
            ]
            Line(points=left_wing, width=screen.dp(2), close=True)
            Line(points=right_wing, width=screen.dp(2), close=True)

            # 驾驶舱
            Color(1, 1, 1, 1)
            cockpit_w = w * 0.27
            cockpit_h = h * 0.31
            Ellipse(pos=(self.center_x - cockpit_w/2, self.center_y - cockpit_h/2),
                   size=(cockpit_w, cockpit_h))

        # 绘制效果
        self._draw_effects()

    def _draw_effects(self) -> None:
        """绘制效果（护盾、无敌）"""
        self.canvas.after.clear()

        with self.canvas.after:
            # 护盾效果
            if self.shield:
                Color(0.2, 1, 1, 0.3)
                shield_margin = screen.dp(10)
                Ellipse(
                    pos=(self.x - shield_margin, self.y - shield_margin),
                    size=(self.width + shield_margin*2, self.height + shield_margin*2)
                )

            # 无敌闪烁
            if self.invincible:
                if int(time.time() * 10) % 2:
                    Color(1, 1, 1, 0.5)
                    Rectangle(pos=self.pos, size=self.size)

    def reset(self) -> None:
        """重置玩家状态"""
        super().reset()
        config = get_config()
        self.health = config.player.max_health
        self.weapon_level = 1
        self.shield = False
        self.shield_time = 0
        self.invincible = False
        self.invincible_time = 0
        self.bombs = 3
        self.lives = 3
