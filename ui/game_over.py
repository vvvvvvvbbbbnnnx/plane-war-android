"""
飞机大战 - 游戏结束界面
"""
from typing import Callable, Optional

from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label

from core.scene import Scene
from systems.audio import audio_manager
from systems.save import save_manager
from utils.helpers import get_chinese_font
from utils.screen import screen


class GameOverScreen(Scene):
    """
    游戏结束界面场景
    """

    def __init__(
        self,
        score: int = 0,
        level: int = 1,
        on_restart: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.score = score
        self.level = level
        self.on_restart = on_restart
        self.on_quit = on_quit
        self._font = get_chinese_font()
        self._create_ui()

    def _create_ui(self) -> None:
        """创建UI"""
        # 半透明背景
        with self.canvas.before:
            Color(0, 0, 0, 0.8)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        # 游戏结束标题
        self.title = Label(
            text='[size=48]游戏结束[/size]',
            markup=True,
            font_size=screen.sp(36),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.75},
            color=(1, 0.3, 0.3, 1),
        )
        self.add_widget(self.title)

        # 分数
        self.score_label = Label(
            text=f'[size=24]最终分数: {self.score}[/size]',
            markup=True,
            font_size=screen.sp(20),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            color=(1, 1, 1, 1),
        )
        self.add_widget(self.score_label)

        # 关卡
        self.level_label = Label(
            text=f'[size=20]到达关卡: {self.level}[/size]',
            markup=True,
            font_size=screen.sp(16),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.52},
            color=(0.8, 0.8, 0.8, 1),
        )
        self.add_widget(self.level_label)

        # 新纪录提示
        high_score = save_manager.get_high_score()
        if self.score > high_score:
            self.new_record_label = Label(
                text='[size=28]新纪录！[/size]',
                markup=True,
                font_size=screen.sp(22),
                font_name=self._font,
                pos_hint={'center_x': 0.5, 'center_y': 0.44},
                color=(1, 1, 0, 1),
            )
            self.add_widget(self.new_record_label)

        # 重新开始按钮
        self.restart_btn = Button(
            text='重新开始',
            font_size=screen.sp(22),
            font_name=self._font,
            size_hint=(0.5, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.32},
            background_color=(0.2, 0.6, 1, 1),
            background_normal='',
        )
        self.restart_btn.bind(on_press=self._on_restart_pressed)
        self.add_widget(self.restart_btn)

        # 返回主菜单按钮
        self.quit_btn = Button(
            text='返回主菜单',
            font_size=screen.sp(20),
            font_name=self._font,
            size_hint=(0.4, 0.06),
            pos_hint={'center_x': 0.5, 'center_y': 0.2},
            background_color=(0.3, 0.3, 0.3, 1),
            background_normal='',
        )
        self.quit_btn.bind(on_press=self._on_quit_pressed)
        self.add_widget(self.quit_btn)

    def _on_restart_pressed(self, instance) -> None:
        """重新开始按钮点击"""
        audio_manager.play_sfx('button')
        if self.on_restart:
            self.on_restart()

    def _on_quit_pressed(self, instance) -> None:
        """退出按钮点击"""
        audio_manager.play_sfx('button')
        if self.on_quit:
            self.on_quit()

    def on_size(self, *args) -> None:
        """窗口大小变化"""
        self._bg_rect.size = self.size
