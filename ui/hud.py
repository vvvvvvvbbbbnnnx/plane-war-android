"""
飞机大战 - HUD（游戏内界面）

显示分数、生命、炸弹等信息
"""
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar

from utils.helpers import get_chinese_font
from utils.screen import screen


class HUD(FloatLayout):
    """
    游戏内HUD

    显示分数、关卡、生命、炸弹、Boss血条等
    """

    score = NumericProperty(0)
    level = NumericProperty(1)
    lives = NumericProperty(3)
    bombs = NumericProperty(3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)

        # 字体
        self._font = get_chinese_font()

        # 创建UI元素
        self._create_ui()

    def _create_ui(self) -> None:
        """创建UI元素"""
        # 分数标签
        self.score_label = Label(
            text='分数: 0',
            font_size=screen.sp(18),
            font_name=self._font,
            size_hint=(None, None),
            size=(screen.rel_w(0.35), screen.rel_h(0.04)),
            pos=(screen.dp(10), screen.real_height - screen.rel_h(0.06)),
            color=(1, 1, 1, 1),
            halign='left',
            valign='middle',
        )
        self.add_widget(self.score_label)

        # 关卡标签
        self.level_label = Label(
            text='关卡: 1',
            font_size=screen.sp(18),
            font_name=self._font,
            size_hint=(None, None),
            size=(screen.rel_w(0.35), screen.rel_h(0.04)),
            pos=(screen.real_width - screen.rel_w(0.35) - screen.dp(10),
                 screen.real_height - screen.rel_h(0.06)),
            color=(1, 1, 1, 1),
            halign='right',
            valign='middle',
        )
        self.add_widget(self.level_label)

        # 生命显示
        self.lives_label = Label(
            text='❤ x 3',
            font_size=screen.sp(16),
            font_name=self._font,
            size_hint=(None, None),
            size=(screen.rel_w(0.25), screen.rel_h(0.03)),
            pos=(screen.dp(10), screen.real_height - screen.rel_h(0.1)),
            color=(1, 0.5, 0.5, 1),
            halign='left',
        )
        self.add_widget(self.lives_label)

        # 炸弹显示
        self.bombs_label = Label(
            text='💣 x 3',
            font_size=screen.sp(16),
            font_name=self._font,
            size_hint=(None, None),
            size=(screen.rel_w(0.25), screen.rel_h(0.03)),
            pos=(screen.real_width - screen.rel_w(0.25) - screen.dp(10),
                 screen.real_height - screen.rel_h(0.1)),
            color=(0.7, 0.7, 0.7, 1),
            halign='right',
        )
        self.add_widget(self.bombs_label)

        # Boss血条（初始隐藏）
        self.boss_health_bar = None
        self.boss_name_label = None

    def update(self, score: int, level: int, lives: int, bombs: int, combo: int = 0) -> None:
        """
        更新HUD显示

        Args:
            score: 分数
            level: 关卡
            lives: 生命
            bombs: 炸弹
        """
        self.score_label.text = f'分数: {score}'
        self.level_label.text = f'关卡: {level}'
        self.lives_label.text = f'❤ x {lives}'
        self.bombs_label.text = f'💣 x {bombs}'
        if combo >= 10:
            self.score_label.text = f'{combo} COMBO! 分数: {score}'
            self.score_label.color = (1, 0.8, 0.2, 1)
        elif combo >= 5:
            self.score_label.color = (1, 1, 0.5, 1)
        else:
            self.score_label.color = (1, 1, 1, 1)

    def show_boss_health(self, boss_name: str = 'Boss') -> None:
        """
        显示Boss血条

        Args:
            boss_name: Boss名称
        """
        if self.boss_health_bar:
            return

        # Boss名称
        self.boss_name_label = Label(
            text=boss_name,
            font_size=screen.sp(14),
            font_name=self._font,
            size_hint=(None, None),
            size=(screen.rel_w(0.3), screen.rel_h(0.03)),
            pos=(screen.real_width / 2 - screen.rel_w(0.15), screen.real_height - screen.rel_h(0.14)),
            color=(1, 0.3, 0.3, 1),
            halign='center',
        )
        self.add_widget(self.boss_name_label)

        # 血条背景
        self.boss_health_bar_bg = ProgressBar(
            max=100,
            value=100,
            size_hint=(None, None),
            size=(screen.rel_w(0.6), screen.dp(10)),
            pos=(screen.real_width / 2 - screen.rel_w(0.3), screen.real_height - screen.rel_h(0.17)),
        )
        self.add_widget(self.boss_health_bar_bg)

        self.boss_health_bar = self.boss_health_bar_bg

    def update_boss_health(self, health_ratio: float) -> None:
        """
        更新Boss血条

        Args:
            health_ratio: 血量比例 (0-1)
        """
        if self.boss_health_bar:
            self.boss_health_bar.value = health_ratio * 100

    def hide_boss_health(self) -> None:
        """隐藏Boss血条"""
        if self.boss_name_label:
            self.remove_widget(self.boss_name_label)
            self.boss_name_label = None

        if self.boss_health_bar:
            self.remove_widget(self.boss_health_bar)
            self.boss_health_bar = None

    def show_message(self, text: str, duration: float = 2.0) -> None:
        """
        显示临时消息

        Args:
            text: 消息文本
            duration: 显示时长
        """
        message = Label(
            text=text,
            font_size=screen.sp(24),
            font_name=self._font,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            color=(1, 1, 0, 1),
        )
        self.add_widget(message)

        # 定时移除
        Clock.schedule_once(lambda dt: self.remove_widget(message), duration)

    def on_size(self, *args) -> None:
        """窗口大小变化时更新UI位置"""
        self.score_label.pos = (screen.dp(10), screen.real_height - screen.rel_h(0.06))
        self.level_label.pos = (screen.real_width - screen.rel_w(0.35) - screen.dp(10),
                                screen.real_height - screen.rel_h(0.06))
        self.lives_label.pos = (screen.dp(10), screen.real_height - screen.rel_h(0.1))
        self.bombs_label.pos = (screen.real_width - screen.rel_w(0.25) - screen.dp(10),
                                screen.real_height - screen.rel_h(0.1))
