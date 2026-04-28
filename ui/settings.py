# -*- coding: utf-8 -*-
"""
飞机大战 - 设置界面
"""
from typing import Optional, Callable
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle

from core.scene import Scene
from utils.screen import screen
from utils.helpers import get_chinese_font
from systems.audio import audio_manager
from systems.save import save_manager


class SettingsScreen(Scene):
    """
    设置界面场景
    """

    def __init__(self, on_back: Optional[Callable] = None, on_close: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.on_back = on_back or on_close
        self._font = get_chinese_font()
        self._create_ui()
        self._load_settings()

    def _create_ui(self) -> None:
        """创建UI"""
        # 背景
        with self.canvas.before:
            Color(0.05, 0.05, 0.15, 1)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)

        # 标题
        self.title = Label(
            text='[size=36]设置[/size]',
            markup=True,
            font_size=screen.sp(28),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.9},
            color=(1, 1, 1, 1),
        )
        self.add_widget(self.title)

        # 音效开关
        self.sound_label = Label(
            text='音效',
            font_size=screen.sp(18),
            font_name=self._font,
            pos_hint={'center_x': 0.3, 'center_y': 0.75},
            color=(1, 1, 1, 1),
            halign='right',
        )
        self.add_widget(self.sound_label)

        self.sound_toggle = ToggleButton(
            text='开',
            font_size=screen.sp(16),
            font_name=self._font,
            size_hint=(0.2, 0.05),
            pos_hint={'center_x': 0.65, 'center_y': 0.75},
            state='down' if audio_manager.enabled else 'normal',
        )
        self.sound_toggle.bind(on_press=self._on_sound_toggle)
        self.add_widget(self.sound_toggle)

        # 音乐音量
        self.music_label = Label(
            text='音乐音量',
            font_size=screen.sp(18),
            font_name=self._font,
            pos_hint={'center_x': 0.3, 'center_y': 0.62},
            color=(1, 1, 1, 1),
            halign='right',
        )
        self.add_widget(self.music_label)

        self.music_slider = Slider(
            min=0, max=1, value=audio_manager.music_volume,
            size_hint=(0.4, 0.05),
            pos_hint={'center_x': 0.6, 'center_y': 0.62},
        )
        self.music_slider.bind(value=self._on_music_volume_change)
        self.add_widget(self.music_slider)

        # 音效音量
        self.sfx_label = Label(
            text='音效音量',
            font_size=screen.sp(18),
            font_name=self._font,
            pos_hint={'center_x': 0.3, 'center_y': 0.52},
            color=(1, 1, 1, 1),
            halign='right',
        )
        self.add_widget(self.sfx_label)

        self.sfx_slider = Slider(
            min=0, max=1, value=audio_manager.sfx_volume,
            size_hint=(0.4, 0.05),
            pos_hint={'center_x': 0.6, 'center_y': 0.52},
        )
        self.sfx_slider.bind(value=self._on_sfx_volume_change)
        self.add_widget(self.sfx_slider)

        # 难度选择
        self.difficulty_label = Label(
            text='难度',
            font_size=screen.sp(18),
            font_name=self._font,
            pos_hint={'center_x': 0.3, 'center_y': 0.4},
            color=(1, 1, 1, 1),
            halign='right',
        )
        self.add_widget(self.difficulty_label)

        # 难度按钮组
        self.easy_btn = Button(
            text='简单',
            font_size=screen.sp(14),
            font_name=self._font,
            size_hint=(0.15, 0.05),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            background_color=(0.3, 0.3, 0.3, 1),
        )
        self.add_widget(self.easy_btn)

        self.normal_btn = Button(
            text='普通',
            font_size=screen.sp(14),
            font_name=self._font,
            size_hint=(0.15, 0.05),
            pos_hint={'center_x': 0.67, 'center_y': 0.4},
            background_color=(0.2, 0.6, 1, 1),
        )
        self.add_widget(self.normal_btn)

        self.hard_btn = Button(
            text='困难',
            font_size=screen.sp(14),
            font_name=self._font,
            size_hint=(0.15, 0.05),
            pos_hint={'center_x': 0.84, 'center_y': 0.4},
            background_color=(0.3, 0.3, 0.3, 1),
        )
        self.add_widget(self.hard_btn)

        # 返回按钮
        self.back_btn = Button(
            text='返回',
            font_size=screen.sp(20),
            font_name=self._font,
            size_hint=(0.4, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.2},
            background_color=(0.3, 0.3, 0.3, 1),
            background_normal='',
        )
        self.back_btn.bind(on_press=self._on_back_pressed)
        self.add_widget(self.back_btn)

    def _load_settings(self) -> None:
        """加载设置"""
        settings = save_manager.load_settings()
        # TODO: 应用设置到UI

    def _save_settings(self) -> None:
        """保存设置"""
        settings = {
            'music_volume': self.music_slider.value,
            'sfx_volume': self.sfx_slider.value,
            'sound_enabled': self.sound_toggle.state == 'down',
        }
        save_manager.save_settings(settings)

    def _on_sound_toggle(self, instance) -> None:
        """音效开关切换"""
        instance.text = '开' if instance.state == 'down' else '关'
        audio_manager.enabled = instance.state == 'down'
        self._save_settings()

    def _on_music_volume_change(self, instance, value) -> None:
        """音乐音量变化"""
        audio_manager.set_music_volume(value)
        self._save_settings()

    def _on_sfx_volume_change(self, instance, value) -> None:
        """音效音量变化"""
        audio_manager.set_sfx_volume(value)
        self._save_settings()

    def _on_back_pressed(self, instance) -> None:
        """返回按钮点击"""
        audio_manager.play_sfx('button')
        if self.on_back:
            self.on_back()

    def on_size(self, *args) -> None:
        """窗口大小变化"""
        self._bg_rect.size = self.size
