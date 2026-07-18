"""
飞机大战 - 主菜单

显示游戏标题、最高分、开始/设置按钮与操作说明。
"""
from typing import Callable, Optional

from kivy.uix.button import Button
from kivy.uix.label import Label

from systems.audio import audio_manager
from systems.save import save_manager
from ui.base import OverlayScene
from utils.helpers import get_chinese_font
from utils.screen import screen


class MainMenu(OverlayScene):
    """主菜单场景"""

    def __init__(self, on_start_game: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.on_start_game = on_start_game
        self._font = get_chinese_font()
        self._create_ui()

    def _create_ui(self) -> None:
        """创建UI：背景、标题、最高分、按钮、操作说明。"""
        # 深色背景
        self._setup_background((0.05, 0.05, 0.15, 1))

        # 标题
        self.title = Label(
            text='[size=48]飞机大战[/size]\n[size=24]Android版[/size]',
            markup=True,
            font_size=screen.sp(36),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.7},
            color=(0.2, 1, 1, 1),
        )
        self.add_widget(self.title)

        # 最高分
        high_score = save_manager.get_high_score()
        self.high_score_label = Label(
            text=f'最高分: {high_score}',
            font_size=screen.sp(16),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
            color=(1, 1, 0, 0.8),
        )
        self.add_widget(self.high_score_label)

        # 开始按钮
        self.start_btn = Button(
            text='开始游戏',
            font_size=screen.sp(22),
            font_name=self._font,
            size_hint=(0.5, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            background_color=(0.2, 0.6, 1, 1),
            background_normal='',
        )
        self.start_btn.bind(on_press=self._on_start_pressed)
        self.add_widget(self.start_btn)

        # 设置按钮
        self.settings_btn = Button(
            text='设置',
            font_size=screen.sp(18),
            font_name=self._font,
            size_hint=(0.3, 0.06),
            pos_hint={'center_x': 0.5, 'center_y': 0.28},
            background_color=(0.3, 0.3, 0.3, 1),
            background_normal='',
        )
        self.settings_btn.bind(on_press=self._on_settings_pressed)
        self.add_widget(self.settings_btn)

        # 操作说明
        self.instructions = Label(
            text='[size=16]触摸屏幕移动飞机\n自动射击\n双击使用炸弹[/size]',
            markup=True,
            font_size=screen.sp(14),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.12},
            color=(0.8, 0.8, 0.8, 1),
        )
        self.add_widget(self.instructions)

    def _on_start_pressed(self, instance) -> None:
        """开始按钮点击：播放音效并触发回调。"""
        audio_manager.play_sfx('button')
        if self.on_start_game:
            self.on_start_game()

    def _on_settings_pressed(self, instance) -> None:
        """设置按钮点击：通过父级 GameWidget 打开设置界面。"""
        audio_manager.play_sfx('button')
        if self.parent and hasattr(self.parent, '_show_settings'):
            self.parent._show_settings()

    def on_enter(self) -> None:
        """进入场景：刷新最高分显示。"""
        super().on_enter()
        self.high_score_label.text = f'最高分: {save_manager.get_high_score()}'
