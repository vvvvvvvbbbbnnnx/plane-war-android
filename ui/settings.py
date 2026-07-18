"""
飞机大战 - 设置界面

提供音效开关、音乐/音效音量、难度选择，并持久化到存档系统。
"""
from typing import Callable, Optional

from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton

from systems.audio import audio_manager
from systems.save import save_manager
from ui.base import OverlayScene
from utils.helpers import get_chinese_font
from utils.screen import screen


class SettingsScreen(OverlayScene):
    """设置界面场景"""

    def __init__(self, on_back: Optional[Callable] = None, on_close: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        # on_back 与 on_close 互为别名，兼容不同调用方
        self.on_back = on_back or on_close
        self._font = get_chinese_font()
        self._difficulty = 'normal'
        self._difficulty_btns = {}
        # _initialized 标记用于避免构建 UI 期间触发控件回调而写存档
        self._initialized = False
        self._create_ui()
        # 延迟加载设置，避免初始化时触发 save
        Clock.schedule_once(lambda dt: self._load_settings(), 0)

    def _create_ui(self) -> None:
        """创建UI：背景、标题、音效开关、音量滑块、难度按钮、返回按钮。"""
        self._setup_background((0.05, 0.05, 0.15, 1))

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
        self.add_widget(Label(
            text='音效',
            font_size=screen.sp(18),
            font_name=self._font,
            pos_hint={'center_x': 0.3, 'center_y': 0.75},
            color=(1, 1, 1, 1),
            halign='right',
        ))
        self.sound_toggle = ToggleButton(
            text='开',
            font_size=screen.sp(16),
            font_name=self._font,
            size_hint=(0.2, 0.05),
            pos_hint={'center_x': 0.65, 'center_y': 0.75},
            state='down',
        )
        self.sound_toggle.bind(on_press=self._on_sound_toggle)
        self.add_widget(self.sound_toggle)

        # 音乐音量
        self.add_widget(Label(
            text='音乐音量',
            font_size=screen.sp(18),
            font_name=self._font,
            pos_hint={'center_x': 0.3, 'center_y': 0.62},
            color=(1, 1, 1, 1),
            halign='right',
        ))
        self.music_slider = Slider(
            min=0, max=1, value=0.7,
            size_hint=(0.4, 0.05),
            pos_hint={'center_x': 0.6, 'center_y': 0.62},
        )
        self.music_slider.bind(value=self._on_music_volume_change)
        self.add_widget(self.music_slider)

        # 音效音量
        self.add_widget(Label(
            text='音效音量',
            font_size=screen.sp(18),
            font_name=self._font,
            pos_hint={'center_x': 0.3, 'center_y': 0.52},
            color=(1, 1, 1, 1),
            halign='right',
        ))
        self.sfx_slider = Slider(
            min=0, max=1, value=0.8,
            size_hint=(0.4, 0.05),
            pos_hint={'center_x': 0.6, 'center_y': 0.52},
        )
        self.sfx_slider.bind(value=self._on_sfx_volume_change)
        self.add_widget(self.sfx_slider)

        # 难度
        self.add_widget(Label(
            text='难度',
            font_size=screen.sp(18),
            font_name=self._font,
            pos_hint={'center_x': 0.3, 'center_y': 0.4},
            color=(1, 1, 1, 1),
            halign='right',
        ))
        # 难度按钮：简单/普通/困难，选中项高亮蓝色
        for text, cx, color in [
            ('简单', 0.5, (0.3, 0.3, 0.3, 1)),
            ('普通', 0.67, (0.2, 0.6, 1, 1)),
            ('困难', 0.84, (0.3, 0.3, 0.3, 1)),
        ]:
            btn = Button(
                text=text,
                font_size=screen.sp(14),
                font_name=self._font,
                size_hint=(0.15, 0.05),
                pos_hint={'center_x': cx, 'center_y': 0.4},
                background_color=color,
            )
            btn.bind(on_press=self._on_difficulty_pressed)
            self._difficulty_btns[text] = btn
            self.add_widget(btn)

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

    def _load_settings(self, *args) -> None:
        """从存档加载设置并同步到控件（仅在初始化完成后才允许写回）。"""
        settings = save_manager.load_settings()
        self._difficulty = settings.get('difficulty', 'normal')
        self.music_slider.value = settings.get('music_volume', 0.7)
        self.sfx_slider.value = settings.get('sfx_volume', 0.8)
        sound_on = settings.get('sound_enabled', True)
        self.sound_toggle.state = 'down' if sound_on else 'normal'
        self.sound_toggle.text = '开' if sound_on else '关'
        audio_manager.enabled = sound_on
        # 高亮当前难度
        if self._difficulty in self._difficulty_btns:
            for btn in self._difficulty_btns.values():
                btn.background_color = (0.3, 0.3, 0.3, 1)
            self._difficulty_btns[self._difficulty].background_color = (0.2, 0.6, 1, 1)
        self._initialized = True

    def _save_settings(self) -> None:
        """持久化当前控件状态到存档（初始化阶段跳过）。"""
        if not self._initialized:
            return
        save_manager.save_settings({
            'music_volume': self.music_slider.value,
            'sfx_volume': self.sfx_slider.value,
            'sound_enabled': self.sound_toggle.state == 'down',
            'difficulty': self._difficulty,
        })

    def _on_difficulty_pressed(self, instance) -> None:
        """难度按钮点击：切换难度并高亮。"""
        audio_manager.play_sfx('button')
        self._difficulty = instance.text
        for btn in self._difficulty_btns.values():
            btn.background_color = (0.3, 0.3, 0.3, 1)
        instance.background_color = (0.2, 0.6, 1, 1)
        self._save_settings()

    def _on_sound_toggle(self, instance) -> None:
        """音效开关切换：同步文本与全局开关。"""
        instance.text = '开' if instance.state == 'down' else '关'
        audio_manager.enabled = instance.state == 'down'
        self._save_settings()

    def _on_music_volume_change(self, instance, value) -> None:
        """音乐音量滑块变化"""
        audio_manager.set_music_volume(value)
        self._save_settings()

    def _on_sfx_volume_change(self, instance, value) -> None:
        """音效音量滑块变化"""
        audio_manager.set_sfx_volume(value)
        self._save_settings()

    def _on_back_pressed(self, instance) -> None:
        """返回按钮点击"""
        audio_manager.play_sfx('button')
        if self.on_back:
            self.on_back()
