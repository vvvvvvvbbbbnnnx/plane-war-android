# -*- coding: utf-8 -*-
"""
飞机大战 - 屏幕适配器

处理不同设备和屏幕尺寸的适配问题。
"""
from typing import Tuple, Optional
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.properties import NumericProperty


class ScreenAdapter:
    """
    屏幕适配器（单例模式）

    提供屏幕尺寸转换、密度独立像素、相对坐标等功能。

    Attributes:
        real_width: 实际屏幕宽度
        real_height: 实际屏幕高度
        scale: 缩放比例
        is_mobile: 是否为移动设备
        is_portrait: 是否为竖屏
    """

    # 设计基准尺寸 (9:16 比例，竖屏)
    DESIGN_WIDTH = 720
    DESIGN_HEIGHT = 1280

    # 缩放限制
    MIN_SCALE = 0.5
    MAX_SCALE = 2.0

    _instance: Optional['ScreenAdapter'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._update_screen_info()

    def _update_screen_info(self) -> None:
        """更新屏幕信息"""
        # 获取实际屏幕尺寸
        self.real_width = Window.width
        self.real_height = Window.height

        # 计算缩放比例
        self.scale_x = self.real_width / self.DESIGN_WIDTH
        self.scale_y = self.real_height / self.DESIGN_HEIGHT
        self.scale = min(self.scale_x, self.scale_y)
        self.scale = max(self.MIN_SCALE, min(self.MAX_SCALE, self.scale))

        # 游戏区域
        self.game_width = self.real_width
        self.game_height = self.real_height

        # 屏幕方向
        self.is_portrait = self.real_height > self.real_width

        # 设备类型判断
        self.is_mobile = platform in ('android', 'ios')
        self.is_android = platform == 'android'
        self.is_ios = platform == 'ios'
        self.is_desktop = platform in ('win', 'macosx', 'linux')

        # 安全区域（用于刘海屏等）
        self.safe_area_top = 0
        self.safe_area_bottom = 0
        self.safe_area_left = 0
        self.safe_area_right = 0

    def update(self) -> None:
        """更新屏幕信息（窗口大小改变时调用）"""
        self._update_screen_info()

    def dp(self, value: float) -> float:
        """
        密度独立像素转换

        Args:
            value: dp值

        Returns:
            实际像素值
        """
        return dp(value) * self.scale

    def sp(self, value: float) -> float:
        """
        缩放独立像素转换（用于字体）

        Args:
            value: sp值

        Returns:
            实际像素值
        """
        return sp(value) * self.scale

    def rel_w(self, ratio: float) -> float:
        """
        相对宽度

        Args:
            ratio: 占屏幕宽度的比例 (0-1)

        Returns:
            实际像素值
        """
        return self.real_width * ratio

    def rel_h(self, ratio: float) -> float:
        """
        相对高度

        Args:
            ratio: 占屏幕高度的比例 (0-1)

        Returns:
            实际像素值
        """
        return self.real_height * ratio

    def rel_x(self, ratio: float) -> float:
        """相对X坐标（rel_w的别名）"""
        return self.rel_w(ratio)

    def rel_y(self, ratio: float) -> float:
        """相对Y坐标（rel_h的别名）"""
        return self.rel_h(ratio)

    def scale_value(self, value: float) -> float:
        """
        缩放数值

        Args:
            value: 基准值

        Returns:
            缩放后的值
        """
        return value * self.scale

    def center(self) -> Tuple[float, float]:
        """
        获取屏幕中心点

        Returns:
            (center_x, center_y)
        """
        return (self.real_width / 2, self.real_height / 2)

    def safe_center(self) -> Tuple[float, float]:
        """
        获取安全区域中心点

        Returns:
            (center_x, center_y)
        """
        safe_width = self.real_width - self.safe_area_left - self.safe_area_right
        safe_height = self.real_height - self.safe_area_top - self.safe_area_bottom
        return (
            self.safe_area_left + safe_width / 2,
            self.safe_area_bottom + safe_height / 2
        )

    def get_safe_rect(self) -> Tuple[float, float, float, float]:
        """
        获取安全区域矩形

        Returns:
            (x, y, width, height)
        """
        return (
            self.safe_area_left,
            self.safe_area_bottom,
            self.real_width - self.safe_area_left - self.safe_area_right,
            self.real_height - self.safe_area_top - self.safe_area_bottom
        )

    def __repr__(self) -> str:
        return (f"ScreenAdapter({self.real_width}x{self.real_height}, "
                f"scale={self.scale:.2f}, mobile={self.is_mobile})")


# 全局屏幕适配器实例
screen = ScreenAdapter()


def get_screen() -> ScreenAdapter:
    """获取全局屏幕适配器实例"""
    return screen


def update_screen() -> None:
    """更新屏幕适配器（窗口大小改变时调用）"""
    global screen
    screen.update()
