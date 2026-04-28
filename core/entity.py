# -*- coding: utf-8 -*-
"""
飞机大战 - 实体基类

提供所有游戏实体的基础类，包含位置、速度、碰撞等通用属性和方法。
"""
from typing import Tuple, Optional, Dict, Any
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.graphics import Color, Rectangle, Ellipse, Line, PushMatrix, PopMatrix, Translate

from utils.screen import screen


class Entity(Widget):
    """
    游戏实体基类

    所有游戏对象（玩家、敌人、子弹等）都继承自此类。
    提供位置、速度、碰撞检测等通用功能。

    Attributes:
        x: X坐标
        y: Y坐标
        width: 宽度
        height: 高度
        velocity_x: X方向速度
        velocity_y: Y方向速度
        active: 是否活动
        entity_type: 实体类型标识
    """

    # 位置属性
    x = NumericProperty(0)
    y = NumericProperty(0)
    width = NumericProperty(0)
    height = NumericProperty(0)

    # 速度属性
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)

    # 状态属性
    active = BooleanProperty(True)
    entity_type = StringProperty('entity')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)

        # 图片组件（可选）
        self._image_widget: Optional[Image] = None
        self._image_source: Optional[str] = None

        # 碰撞边界偏移（用于自定义碰撞盒）
        self._hitbox_offset_x = 0
        self._hitbox_offset_y = 0
        self._hitbox_scale = 1.0

    def set_size_rel(self, width_ratio: float, height_ratio: float) -> None:
        """
        使用相对比例设置尺寸

        Args:
            width_ratio: 宽度占屏幕宽度的比例 (0-1)
            height_ratio: 高度占屏幕高度的比例 (0-1)
        """
        self.size = (screen.rel_w(width_ratio), screen.rel_h(height_ratio))

    def set_position(self, x: float, y: float) -> None:
        """
        设置位置

        Args:
            x: X坐标
            y: Y坐标
        """
        self.pos = (x, y)

    def setup_image(self, source: str, allow_stretch: bool = True,
                    keep_ratio: bool = True) -> bool:
        """
        设置图片资源

        Args:
            source: 图片路径
            allow_stretch: 是否允许拉伸
            keep_ratio: 是否保持宽高比

        Returns:
            是否成功加载图片
        """
        from utils.resources import ResourceManager

        # 检查资源是否存在
        if not ResourceManager.exists(source):
            return False

        self._image_source = source

        # 创建图片组件
        self._image_widget = Image(
            source=source,
            allow_stretch=allow_stretch,
            keep_ratio=keep_ratio,
            size=self.size,
            pos=self.pos,
            size_hint=(None, None)
        )
        self.add_widget(self._image_widget)
        return True

    def update_image_position(self) -> None:
        """更新图片组件位置"""
        if self._image_widget:
            self._image_widget.pos = self.pos
            self._image_widget.size = self.size

    def on_pos(self, instance, value) -> None:
        """位置变化时更新图片"""
        self.update_image_position()

    def on_size(self, instance, value) -> None:
        """大小变化时更新图片"""
        self.update_image_position()

    def update(self, dt: float) -> None:
        """
        更新实体状态

        Args:
            dt: 时间增量（秒）
        """
        if not self.active:
            return

        # 更新位置
        self.x += self.velocity_x * dt * 60  # 标准化为60FPS
        self.y += self.velocity_y * dt * 60

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        获取碰撞边界

        Returns:
            (x, y, width, height) 碰撞盒边界
        """
        w = self.width * self._hitbox_scale
        h = self.height * self._hitbox_scale
        x = self.x + self._hitbox_offset_x + (self.width - w) / 2
        y = self.y + self._hitbox_offset_y + (self.height - h) / 2
        return (x, y, w, h)

    def get_center(self) -> Tuple[float, float]:
        """
        获取中心点坐标

        Returns:
            (center_x, center_y) 中心点
        """
        return (self.x + self.width / 2, self.y + self.height / 2)

    def set_center(self, x: float, y: float) -> None:
        """
        设置中心点位置

        Args:
            x: 中心X坐标
            y: 中心Y坐标
        """
        self.x = x - self.width / 2
        self.y = y - self.height / 2

    def collides_with(self, other: 'Entity') -> bool:
        """
        检测与另一个实体的碰撞

        Args:
            other: 另一个实体

        Returns:
            是否碰撞
        """
        if not self.active or not other.active:
            return False

        b1 = self.get_bounds()
        b2 = other.get_bounds()

        return (b1[0] < b2[0] + b2[2] and
                b1[0] + b1[2] > b2[0] and
                b1[1] < b2[1] + b2[3] and
                b1[1] + b1[3] > b2[1])

    def is_on_screen(self, margin: float = 0) -> bool:
        """
        检测是否在屏幕内

        Args:
            margin: 边界余量

        Returns:
            是否在屏幕内
        """
        return (self.x + self.width > -margin and
                self.x < screen.real_width + margin and
                self.y + self.height > -margin and
                self.y < screen.real_height + margin)

    def reset(self) -> None:
        """
        重置实体状态（用于对象池）

        子类应重写此方法以重置特定状态
        """
        self.active = True
        self.velocity_x = 0
        self.velocity_y = 0
        self._hitbox_offset_x = 0
        self._hitbox_offset_y = 0
        self._hitbox_scale = 1.0

    def draw(self) -> None:
        """
        绘制实体

        子类应重写此方法以实现自定义绘制
        如果使用了图片，则不需要重写
        """
        pass

    def dispose(self) -> None:
        """
        清理资源

        在实体被移除时调用
        """
        if self._image_widget and self.parent:
            self.remove_widget(self._image_widget)
        self._image_widget = None
        self._image_source = None


class SpriteEntity(Entity):
    """
    精灵实体类

    支持精灵图集和动画的实体基类
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 动画相关
        self._frames: list = []
        self._current_frame: int = 0
        self._animation_speed: float = 0.1  # 秒/帧
        self._animation_timer: float = 0
        self._loop_animation: bool = True
        self._playing: bool = False

    def load_frames(self, frame_paths: list, auto_play: bool = True) -> bool:
        """
        加载动画帧

        Args:
            frame_paths: 帧图片路径列表
            auto_play: 是否自动播放

        Returns:
            是否成功加载
        """
        from utils.resources import ResourceManager

        self._frames = []
        for path in frame_paths:
            if ResourceManager.exists(path):
                self._frames.append(path)

        if not self._frames:
            return False

        # 设置第一帧
        self._current_frame = 0
        self.setup_image(self._frames[0])

        if auto_play:
            self.play_animation()

        return True

    def play_animation(self, speed: float = None, loop: bool = True) -> None:
        """
        播放动画

        Args:
            speed: 动画速度（秒/帧）
            loop: 是否循环
        """
        if speed is not None:
            self._animation_speed = speed
        self._loop_animation = loop
        self._playing = True
        self._animation_timer = 0

    def stop_animation(self) -> None:
        """停止动画"""
        self._playing = False

    def update(self, dt: float) -> None:
        """更新实体和动画"""
        super().update(dt)

        if self._playing and len(self._frames) > 1:
            self._animation_timer += dt
            if self._animation_timer >= self._animation_speed:
                self._animation_timer = 0
                self._current_frame += 1

                if self._current_frame >= len(self._frames):
                    if self._loop_animation:
                        self._current_frame = 0
                    else:
                        self._current_frame = len(self._frames) - 1
                        self._playing = False

                # 更新图片
                if self._image_widget:
                    self._image_widget.source = self._frames[self._current_frame]

    def reset(self) -> None:
        """重置状态"""
        super().reset()
        self._current_frame = 0
        self._animation_timer = 0
        self._playing = False
