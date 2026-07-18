"""
飞机大战 - UI 覆盖层基类

主菜单 / 暂停菜单 / 结算界面 / 设置界面 共享相同的背景矩形绘制与
窗口尺寸同步逻辑，提取到 ``OverlayScene`` 中以消除重复代码。
"""
from kivy.graphics import Color, Rectangle

from core.scene import Scene


class OverlayScene(Scene):
    """
    带全屏背景的覆盖层场景基类

    子类在构建 UI 时调用 ``_setup_background(color)`` 即可绘制背景矩形，
    ``on_size`` 时自动同步背景矩形的位置与尺寸。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._bg_rect = None

    def _setup_background(self, color: tuple[float, float, float, float]) -> None:
        """在 ``canvas.before`` 中绘制全屏背景矩形（位于所有子 widget 之下）。

        Args:
            color: (r, g, b, a) 背景颜色
        """
        with self.canvas.before:
            Color(*color)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

    def on_size(self, *args) -> None:
        """窗口尺寸变化时同步背景矩形的位置与尺寸。"""
        if self._bg_rect:
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size
