# -*- coding: utf-8 -*-
"""
飞机大战 - 暂停菜单
"""
from typing import Optional, Callable
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle

from core.scene import Scene
from utils.screen import screen
from utils.helpers import get_chinese_font


class PauseMenu(Scene):
    """
    暂停菜单场景
    """

    def __init__(
        self,
        on_resume: Optional[Callable] = None,
        on_restart: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.on_resume = on_resume
        self.on_restart = on_restart
        self.on_quit = on_quit
        self._font = get_chinese_font()
        self._create_ui()

    def _create_ui(self) -> None:
        """创建UI"""
        # 半透明背景
        with self.canvas.before:
            Color(0, 0, 0, 0.7)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        # 标题
        self.title = Label(
            text='[size=36]游戏暂停[/size]',
            markup=True,
            font_size=screen.sp(28),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.7},
            color=(1, 1, 1, 1),
        )
        self.add_widget(self.title)

        # 继续按钮
        self.resume_btn = Button(
            text='继续游戏',
            font_size=screen.sp(20),
            font_name=self._font,
            size_hint=(0.5, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0.2, 0.8, 0.2, 1),
            background_normal='',
        )
        self.resume_btn.bind(on_press=self._on_resume_pressed)
        self.add_widget(self.resume_btn)

        # 重新开始按钮
        self.restart_btn = Button(
            text='重新开始',
            font_size=screen.sp(20),
            font_name=self._font,
            size_hint=(0.5, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.38},
            background_color=(0.2, 0.6, 1, 1),
            background_normal='',
        )
        self.restart_btn.bind(on_press=self._on_restart_pressed)
        self.add_widget(self.restart_btn)

        # 退出按钮
        self.quit_btn = Button(
            text='返回主菜单',
            font_size=screen.sp(20),
            font_name=self._font,
            size_hint=(0.5, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.26},
            background_color=(0.8, 0.2, 0.2, 1),
            background_normal='',
        )
        self.quit_btn.bind(on_press=self._on_quit_pressed)
        self.add_widget(self.quit_btn)

    def _on_resume_pressed(self, instance) -> None:
        """继续按钮点击"""
        from systems.audio import audio_manager
        audio_manager.play_sfx('button')
        if self.on_resume:
            self.on_resume()

    def _on_restart_pressed(self, instance) -> None:
        """重新开始按钮点击"""
        from systems.audio import audio_manager
        audio_manager.play_sfx('button')
        if self.on_restart:
            self.on_restart()

    def _on_quit_pressed(self, instance) -> None:
        """退出按钮点击"""
        from systems.audio import audio_manager
        audio_manager.play_sfx('button')
        if self.on_quit:
            self.on_quit()

    def on_size(self, *args) -> None:
        """窗口大小变化"""
        self._bg_rect.size = self.size
