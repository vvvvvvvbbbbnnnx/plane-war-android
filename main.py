"""
飞机大战 - 入口文件

启动游戏并初始化所有系统。

职责划分
--------
* ``PlaneWarApp``  —— Kivy App，负责窗口/配置/音效系统初始化与生命周期。
* ``GameWidget``   —— 游戏主界面容器，协调背景、UI 覆盖层（菜单/HUD/暂停/结算/设置）、
  触摸与键盘路由、以及玩家 widget 的挂载；实体 widget 的挂载/卸载由 ``Game`` 统一管理。
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image

from config.settings import get_config
from core.game import GameState, game
from systems.audio import audio_manager
from ui.game_over import GameOverScreen
from ui.hud import HUD
from ui.menu import MainMenu
from ui.pause import PauseMenu
from ui.settings import SettingsScreen
from utils.resources import ResourceManager
from utils.screen import update_screen

# 音效文件名 → 资源文件映射（仅在对应文件存在时加载）
# 抽取为模块常量，便于查阅与维护，避免散落在初始化方法中。
_SOUND_FILES: dict[str, str] = {
    'shoot': 'shoot.wav',
    'explosion': 'explosion.wav',
    'powerup': 'powerup.wav',
    'hit': 'hit.wav',
    'bomb': 'bomb.wav',
    'boss_appear': 'boss.wav',
    'boss_death': 'boss_death.wav',
    'button': 'button.wav',
    'bgm': 'bgm.wav',
}


class GameWidget(FloatLayout):
    """
    游戏主界面容器

    管理所有游戏元素和UI的显示。本身不持有游戏逻辑，逻辑由 ``Game`` 单例负责；
    本类负责：滚动背景、UI 覆盖层的添加/移除、触摸与键盘事件路由、玩家 widget 挂载。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 游戏实例
        self.game = game
        game.root_widget = self

        # 背景
        self._setup_background()

        # UI组件（按需创建）
        self.hud: HUD = None
        self.menu: MainMenu = None
        self.pause_menu: PauseMenu = None
        self.game_over_screen: GameOverScreen = None
        self.settings_screen: SettingsScreen = None

        # 显示主菜单
        self._show_main_menu()

        # 启动游戏循环（60 FPS）
        Clock.schedule_interval(self._update, 1/60)

        # 绑定窗口大小变化与键盘事件
        Window.bind(on_resize=self._on_window_resize)
        Window.bind(on_keyboard=self._on_keyboard)

    def _setup_background(self) -> None:
        """设置滚动背景：双图拼接实现无缝滚动；无背景图时使用纯色。"""
        bg_path = ResourceManager.get_image_path('background.png')
        if bg_path:
            # 创建两个背景实现滚动效果（上下拼接，循环位移）
            self.bg1 = Image(
                source=bg_path,
                allow_stretch=True,
                keep_ratio=False,
                size_hint=(None, None),
                size=(Window.width, Window.height * 2),
                pos=(0, 0)
            )
            self.bg2 = Image(
                source=bg_path,
                allow_stretch=True,
                keep_ratio=False,
                size_hint=(None, None),
                size=(Window.width, Window.height * 2),
                pos=(0, Window.height)
            )
            self.add_widget(self.bg1)
            self.add_widget(self.bg2)
            self.bg_scroll_speed = 1.0  # 滚动速度
        else:
            # 使用黑色背景
            with self.canvas.before:
                Color(0.02, 0.02, 0.08, 1)
                self.bg_rect = Rectangle(pos=(0, 0), size=Window.size)

    def _show_main_menu(self) -> None:
        """显示主菜单"""
        self.menu = MainMenu(on_start_game=self._start_game)
        self.add_widget(self.menu)

    def _show_settings(self) -> None:
        """显示设置界面"""
        self.settings_screen = SettingsScreen(on_close=self._close_settings)
        self.add_widget(self.settings_screen)

    def _close_settings(self) -> None:
        """关闭设置界面"""
        if self.settings_screen:
            self.remove_widget(self.settings_screen)
            self.settings_screen = None

    def _start_game(self) -> None:
        """开始游戏：移除菜单、创建HUD、启动游戏逻辑、挂载玩家。"""
        # 移除菜单
        if self.menu:
            self.remove_widget(self.menu)
            self.menu = None

        # 创建HUD
        self.hud = HUD()
        self.add_widget(self.hud)

        # 开始游戏
        self.game.start_game()

        # 添加玩家到界面（玩家 widget 由 main.py 挂载，其余实体由 game 管理）
        if self.game.player:
            self.add_widget(self.game.player)

    def _update(self, dt: float) -> None:
        """游戏主更新循环：滚动背景 + 游戏逻辑 + HUD + 结算检测。"""
        # 更新滚动背景
        self._update_background(dt)

        if self.game.state == GameState.PLAYING:
            # 更新游戏逻辑（实体的 widget 挂载/卸载已内联在 game.py 的生命周期中）
            self.game.update(dt)

            # 更新HUD
            if self.hud and self.game.player:
                self.hud.update(
                    score=self.game.score,
                    level=self.game.level,
                    lives=self.game.player.lives,
                    bombs=self.game.player.bombs,
                    combo=getattr(self.game, 'combo', 0)
                )

                # 更新Boss血条
                if self.game.boss:
                    self.hud.show_boss_health(f'Boss Lv.{self.game.level}')
                    self.hud.update_boss_health(self.game.boss.get_health_ratio())
                else:
                    self.hud.hide_boss_health()

            # 检查游戏结束
            if self.game.state == GameState.GAME_OVER:
                self._show_game_over()

    def _update_background(self, dt: float) -> None:
        """更新滚动背景：双图循环位移。"""
        if hasattr(self, 'bg1') and hasattr(self, 'bg2'):
            # 滚动背景
            scroll = self.bg_scroll_speed * dt * 60
            self.bg1.y -= scroll
            self.bg2.y -= scroll

            # 循环滚动：完全离开屏幕后重置到顶部
            if self.bg1.y <= -Window.height:
                self.bg1.y = Window.height
            if self.bg2.y <= -Window.height:
                self.bg2.y = Window.height

    def _fix_z_order(self) -> None:
        """确保图层顺序: 背景 → 道具 → 敌机 → Boss → 子弹 → 玩家 → 爆炸 → HUD

        由 Game._attach_entity 在挂载新实体时按需调用，避免每帧全量扫描。
        """
        # 将玩家移到 HUD 之下、其他实体之上
        if self.game.player and self.game.player.parent:
            self.remove_widget(self.game.player)
            self.add_widget(self.game.player)

        # 爆炸移到玩家之上
        for exp in self.game.explosions:
            if exp.active and exp.parent:
                self.remove_widget(exp)
                self.add_widget(exp)

        # HUD 始终在最上层
        if self.hud and self.hud.parent:
            self.remove_widget(self.hud)
            self.add_widget(self.hud)

    def _show_game_over(self) -> None:
        """显示游戏结束界面"""
        self.game_over_screen = GameOverScreen(
            score=self.game.score,
            level=self.game.level,
            on_restart=self._restart_game,
            on_quit=self._quit_to_menu
        )
        self.add_widget(self.game_over_screen)

    def _restart_game(self) -> None:
        """重新开始游戏：移除结算界面、清理实体、重新开始、挂载玩家。"""
        # 移除游戏结束界面
        if self.game_over_screen:
            self.remove_widget(self.game_over_screen)
            self.game_over_screen = None

        # 清理旧实体
        self._clear_game_entities()

        # 重新开始
        self.game.start_game()

        # 添加玩家
        if self.game.player:
            self.add_widget(self.game.player)

    def _quit_to_menu(self) -> None:
        """返回主菜单：移除结算界面与HUD、清理实体、显示主菜单。"""
        # 移除游戏结束界面
        if self.game_over_screen:
            self.remove_widget(self.game_over_screen)
            self.game_over_screen = None

        # 移除HUD
        if self.hud:
            self.remove_widget(self.hud)
            self.hud = None

        # 清理游戏实体
        self._clear_game_entities()

        # 显示主菜单
        self._show_main_menu()

    def _clear_game_entities(self) -> None:
        """清理游戏实体 widget（逻辑清理由 game._clear_all_entities 负责）。

        职责边界：玩家 widget 由 main.py 挂载，单独卸载；
        其余实体 widget 由 game._attach_entity/_detach_entity 维护，此处统一卸载。
        """
        # 玩家 widget 由 main.py 挂载，单独卸载
        if self.game.player and self.game.player.parent:
            self.remove_widget(self.game.player)
        # 其余实体 widget 由 game._attach_entity/_detach_entity 维护，统一卸载
        for entity in (
            *self.game.enemies,
            *self.game.bullets,
            *self.game.powerups,
            *self.game.explosions,
        ):
            if entity.parent:
                self.remove_widget(entity)
        if self.game.boss and self.game.boss.parent:
            self.remove_widget(self.game.boss)

    def _show_pause_menu(self) -> None:
        """显示暂停菜单"""
        self.game.pause_game()
        self.pause_menu = PauseMenu(
            on_resume=self._resume_game,
            on_restart=self._restart_game,
            on_quit=self._quit_to_menu
        )
        self.add_widget(self.pause_menu)

    def _resume_game(self) -> None:
        """恢复游戏"""
        if self.pause_menu:
            self.remove_widget(self.pause_menu)
            self.pause_menu = None
        self.game.resume_game()

    def _on_window_resize(self, instance, width, height) -> None:
        """窗口大小变化：更新屏幕适配器与背景矩形。"""
        update_screen()
        if hasattr(self, 'bg_rect'):
            self.bg_rect.size = (width, height)

    def _on_keyboard(self, window, key, *args) -> bool:
        """键盘事件：ESC 切换暂停/恢复。"""
        if key == 27:  # ESC键
            if self.game.state == GameState.PLAYING:
                self._show_pause_menu()
                return True
            elif self.game.state == GameState.PAUSED:
                self._resume_game()
                return True
        return False

    def on_touch_down(self, touch) -> bool:
        """触摸按下：游戏中交给游戏处理，否则交给UI。"""
        if self.game.state == GameState.PLAYING:
            return self.game.on_touch_down(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch) -> bool:
        """触摸移动：游戏中交给游戏处理，否则交给UI。"""
        if self.game.state == GameState.PLAYING:
            return self.game.on_touch_move(touch)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch) -> bool:
        """触摸抬起：游戏中交给游戏处理，否则交给UI。"""
        if self.game.state == GameState.PLAYING:
            return self.game.on_touch_up(touch)
        return super().on_touch_up(touch)


class PlaneWarApp(App):
    """飞机大战应用"""

    def build(self):
        # 设置全屏
        Window.fullscreen = 'auto'

        # 加载配置
        get_config()

        # 初始化音效系统
        self._init_audio()

        return GameWidget()

    def _init_audio(self) -> None:
        """初始化音效系统：按 ``_SOUND_FILES`` 加载存在的音效文件。"""
        sound_config = {}
        for name, filename in _SOUND_FILES.items():
            path = ResourceManager.get_sound_path(filename)
            if path:
                sound_config[name] = path

        if sound_config:
            audio_manager.load_sounds(sound_config)

    def on_pause(self) -> bool:
        """应用暂停（Android 生命周期）：暂停游戏。"""
        if self.root and hasattr(self.root, 'game'):
            self.root.game.pause_game()
        return True

    def on_resume(self) -> None:
        """应用恢复（Android 生命周期）：恢复游戏。"""
        if self.root and hasattr(self.root, 'game'):
            self.root.game.resume_game()


if __name__ == '__main__':
    PlaneWarApp().run()
