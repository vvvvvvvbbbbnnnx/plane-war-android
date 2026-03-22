# -*- coding: utf-8 -*-
"""
飞机大战 - Android版 (图片资源版)
使用 Kivy 框架，支持各种屏幕尺寸
"""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.image import Image as CoreImage
import random
import math
import os

# 获取资源路径
def get_resource_path(filename):
    """获取资源文件的绝对路径"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)


class ScreenAdapter:
    """屏幕适配器 - 处理不同设备的屏幕适配"""

    # 设计基准尺寸 (9:16 比例，竖屏)
    DESIGN_WIDTH = 480
    DESIGN_HEIGHT = 854

    # 最小/最大缩放限制
    MIN_SCALE = 0.5
    MAX_SCALE = 2.0

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

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

        print(f"[ScreenAdapter] 屏幕: {self.real_width}x{self.real_height}")
        print(f"[ScreenAdapter] 缩放: {self.scale:.2f}, 移动端: {self.is_mobile}")

    def dp(self, value):
        """密度独立像素转换"""
        return dp(value) * self.scale

    def sp(self, value):
        """缩放独立像素转换 (用于字体)"""
        return sp(value) * self.scale

    def rel_x(self, ratio):
        """相对X坐标 (0-1)"""
        return self.real_width * ratio

    def rel_y(self, ratio):
        """相对Y坐标 (0-1)"""
        return self.real_height * ratio

    def scale_value(self, value):
        """缩放数值"""
        return value * self.scale


# 全局屏幕适配器
screen = ScreenAdapter()


class SpriteWidget(Widget):
    """精灵组件基类 - 支持图片"""

    image_source = StringProperty(None)
    use_image = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self._image_widget = None
        self._canvas_initialized = False

    def set_size_rel(self, width_ratio, height_ratio):
        """使用相对比例设置尺寸"""
        self.size = (screen.rel_x(width_ratio), screen.rel_y(height_ratio))

    def set_size_dp(self, width, height):
        """使用dp设置尺寸"""
        self.size = (screen.dp(width), screen.dp(height))

    def setup_image(self, source, allow_stretch=True, keep_ratio=True):
        """设置图片"""
        if not self.use_image or not source:
            return False

        try:
            # 检查文件是否存在
            if not os.path.exists(source):
                print(f"[Warning] 图片不存在: {source}")
                return False

            self.image_source = source
            self._image_widget = Image(
                source=source,
                allow_stretch=allow_stretch,
                keep_ratio=keep_ratio,
                size=self.size,
                pos=self.pos
            )
            self.add_widget(self._image_widget)
            self._canvas_initialized = True
            return True
        except Exception as e:
            print(f"[Error] 加载图片失败 {source}: {e}")
            return False

    def update_image_pos(self):
        """更新图片位置"""
        if self._image_widget:
            self._image_widget.pos = self.pos
            self._image_widget.size = self.size

    def on_pos(self, *args):
        self.update_image_pos()

    def on_size(self, *args):
        self.update_image_pos()


class Player(SpriteWidget):
    """玩家飞机 - 图片版"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 使用相对尺寸
        self.set_size_rel(0.125, 0.094)  # 60/480, 80/854

        self.health = 3
        self.max_health = 3
        self.weapon_level = 1
        self.shield = False
        self.shield_time = 0
        self.invincible = False
        self.invincible_time = 0
        self.speed = screen.scale_value(8)

        # 尝试加载图片
        self._image_loaded = self.setup_image(
            get_resource_path('plane_sprite/png/Plane/Fly (1).png')
        )

        # 如果没有图片，使用绘制
        if not self._image_loaded:
            self.draw_ship()

    def draw_ship(self):
        """绘制飞机（备用）"""
        if self._image_loaded:
            return

        self.canvas.clear()
        with self.canvas:
            # 主体
            Color(0.2, 1, 1, 1)
            w, h = self.size
            body_points = [
                (self.center_x, self.top),
                (self.x + w * 0.17, self.y + h * 0.25),
                (self.x + w * 0.08, self.y),
                (self.right - w * 0.08, self.y),
                (self.right - w * 0.17, self.y + h * 0.25),
            ]
            Line(points=body_points, width=screen.dp(2), close=True)

            # 机翼
            Color(0.2, 0.6, 1, 1)
            left_wing = [
                (self.x + w * 0.17, self.y + h * 0.375),
                (self.x, self.y + h * 0.125),
                (self.x + w * 0.25, self.y + h * 0.25),
            ]
            right_wing = [
                (self.right - w * 0.17, self.y + h * 0.375),
                (self.right, self.y + h * 0.125),
                (self.right - w * 0.25, self.y + h * 0.25),
            ]
            Line(points=left_wing, width=screen.dp(2), close=True)
            Line(points=right_wing, width=screen.dp(2), close=True)

            # 驾驶舱
            Color(1, 1, 1, 1)
            cockpit_w = w * 0.27
            cockpit_h = h * 0.31
            Ellipse(pos=(self.center_x - cockpit_w/2, self.center_y - cockpit_h/2),
                   size=(cockpit_w, cockpit_h))

            # 护盾效果
            if self.shield:
                Color(0.2, 1, 1, 0.3)
                shield_margin = screen.dp(10)
                Ellipse(pos=(self.x - shield_margin, self.y - shield_margin),
                       size=(self.width + shield_margin*2, self.height + shield_margin*2))

            # 无敌闪烁
            if self.invincible and int(Clock.get_time() * 10) % 2:
                Color(1, 1, 1, 0.5)
                Rectangle(pos=self.pos, size=self.size)

    def update_effects(self):
        """更新效果（护盾、无敌）"""
        if self._image_loaded:
            # 如果使用了图片，在 canvas 上绘制效果
            self.canvas.after.clear()
            with self.canvas.after:
                if self.shield:
                    Color(0.2, 1, 1, 0.3)
                    shield_margin = screen.dp(10)
                    Ellipse(pos=(self.x - shield_margin, self.y - shield_margin),
                           size=(self.width + shield_margin*2, self.height + shield_margin*2))

                if self.invincible and int(Clock.get_time() * 10) % 2:
                    Color(1, 1, 1, 0.5)
                    Rectangle(pos=self.pos, size=self.size)
        else:
            self.draw_ship()


class Enemy(SpriteWidget):
    """敌机 - 图片版"""
    enemy_type = 'normal'

    def __init__(self, enemy_type='normal', **kwargs):
        super().__init__(**kwargs)
        self.enemy_type = enemy_type
        self.setup_type()

    def setup_type(self):
        if self.enemy_type == 'normal':
            self.set_size_rel(0.083, 0.047)  # 40/480, 40/854
            self.health = 1
            self.speed = screen.scale_value(3)
            self.score = 100
            self.color = (1, 0.2, 0.2)
            image_file = 'plane_sprite/png/Plane/Dead (1).png'
        elif self.enemy_type == 'fast':
            self.set_size_rel(0.0625, 0.041)  # 30/480, 35/854
            self.health = 1
            self.speed = screen.scale_value(5)
            self.score = 150
            self.color = (0.8, 0.4, 1)
            image_file = 'plane_sprite/png/Plane/Fly (2).png'
        elif self.enemy_type == 'tank':
            self.set_size_rel(0.115, 0.059)  # 55/480, 50/854
            self.health = 3
            self.speed = screen.scale_value(2)
            self.score = 300
            self.color = (0.4, 0.4, 0.4)
            image_file = 'plane_sprite/png/Plane/Shoot (1).png'

        # 尝试加载图片
        self._image_loaded = self.setup_image(
            get_resource_path(image_file)
        )

    def draw_ship(self):
        """绘制敌机（备用）"""
        if self._image_loaded:
            return

        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            Color(*self.color)
            if self.enemy_type == 'normal':
                points = [
                    (self.center_x, self.y),
                    (self.x, self.top - h * 0.25),
                    (self.center_x, self.top - h * 0.5),
                    (self.right, self.top - h * 0.25),
                ]
                Line(points=points, width=screen.dp(2), close=True)
            elif self.enemy_type == 'fast':
                points = [
                    (self.center_x, self.y),
                    (self.x, self.top),
                    (self.center_x, self.top - h * 0.25),
                    (self.right, self.top),
                ]
                Line(points=points, width=screen.dp(2), close=True)
            elif self.enemy_type == 'tank':
                Rectangle(pos=(self.x + w*0.1, self.y + h*0.1),
                         size=(w * 0.8, h * 0.8))
                Color(0.6, 0.2, 0.2)
                Rectangle(pos=(self.x + w*0.2, self.y + h*0.2),
                         size=(w * 0.6, h * 0.6))


class Boss(SpriteWidget):
    """Boss - 图片版"""

    def __init__(self, level=1, **kwargs):
        super().__init__(**kwargs)
        self.level = level
        # Boss尺寸随关卡增加
        base_w = 0.25 + level * 0.02
        base_h = 0.1 + level * 0.01
        self.set_size_rel(min(base_w, 0.4), min(base_h, 0.15))

        self.health = 20 + level * 10
        self.max_health = self.health
        self.speed = screen.scale_value(1.5)
        self.score = 1000 * level
        self.direction = 1
        self.shoot_timer = 0

        # 尝试加载图片
        self._image_loaded = self.setup_image(
            get_resource_path('plane_sprite/png/Plane/Shoot (5).png')
        )

    def draw_ship(self):
        """绘制Boss（备用）"""
        if self._image_loaded:
            # 绘制血条
            self.canvas.after.clear()
            w, h = self.size
            with self.canvas.after:
                bar_height = screen.dp(8)
                Color(0.3, 0.3, 0.3)
                Rectangle(pos=(self.x, self.top + screen.dp(5)),
                         size=(w, bar_height))
                Color(1, 0, 0)
                health_ratio = self.health / self.max_health
                Rectangle(pos=(self.x, self.top + screen.dp(5)),
                         size=(w * health_ratio, bar_height))
            return

        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            # 主体
            Color(0.5, 0, 0)
            Ellipse(pos=self.pos, size=self.size)
            Color(0.8, 0.2, 0.2)
            Ellipse(pos=(self.x + w*0.08, self.y + h*0.06),
                   size=(w * 0.84, h * 0.88))

            # 核心
            Color(1, 0.84, 0)
            core_size = min(w, h) * 0.3
            Ellipse(pos=(self.center_x - core_size/2, self.center_y - core_size/2),
                   size=(core_size, core_size))

            # 血条
            bar_height = screen.dp(8)
            Color(0.3, 0.3, 0.3)
            Rectangle(pos=(self.x, self.top + screen.dp(5)),
                     size=(w, bar_height))
            Color(1, 0, 0)
            health_ratio = self.health / self.max_health
            Rectangle(pos=(self.x, self.top + screen.dp(5)),
                     size=(w * health_ratio, bar_height))


class Bullet(SpriteWidget):
    """子弹 - 图片版"""

    def __init__(self, is_player=True, **kwargs):
        super().__init__(**kwargs)
        self.is_player = is_player
        if is_player:
            self.set_size_rel(0.017, 0.023)  # 8/480, 20/854
            self.speed = screen.scale_value(12)
            self.color = (0.2, 1, 1)
            image_file = 'plane_sprite/png/Bullet/Bullet (1).png'
        else:
            self.set_size_rel(0.021, 0.018)  # 10/480, 15/854
            self.speed = screen.scale_value(4)
            self.color = (1, 0.3, 0.3)
            image_file = 'plane_sprite/png/Bullet/Bullet (5).png'

        # 尝试加载图片
        self._image_loaded = self.setup_image(
            get_resource_path(image_file)
        )

    def draw_bullet(self):
        """绘制子弹（备用）"""
        if self._image_loaded:
            return

        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            Ellipse(pos=self.pos, size=self.size)


class PowerUp(SpriteWidget):
    """道具 - 图片版"""
    powerup_type = 'health'

    def __init__(self, powerup_type='health', **kwargs):
        super().__init__(**kwargs)
        self.powerup_type = powerup_type
        self.set_size_rel(0.073, 0.041)  # 35/480, 35/854
        self.speed = screen.scale_value(2)
        self.colors = {
            'health': (0.2, 1, 0.4),
            'weapon': (1, 1, 0.2),
            'shield': (0.2, 1, 1),
            'bomb': (0.5, 0.5, 0.5),
        }

        # 道具使用图形绘制，不使用图片
        self.use_image = False
        self.draw_item()

    def draw_item(self):
        """绘制道具"""
        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            Color(*self.colors.get(self.powerup_type, (1, 1, 1)))
            Ellipse(pos=self.pos, size=self.size)

            if self.powerup_type == 'health':
                # 十字
                Color(1, 1, 1)
                cross_w = w * 0.15
                cross_h = h * 0.6
                Rectangle(pos=(self.center_x - cross_w/2, self.y + h*0.2),
                         size=(cross_w, cross_h))
                Rectangle(pos=(self.x + w*0.2, self.center_y - cross_w/2),
                         size=(cross_h, cross_w))
            elif self.powerup_type == 'weapon':
                # 闪电
                Color(1, 0.84, 0)
                points = [
                    (self.center_x + w*0.1, self.top - h*0.1),
                    (self.x + w*0.25, self.center_y),
                    (self.center_x, self.center_y),
                    (self.center_x - w*0.1, self.y + h*0.1),
                    (self.right - w*0.25, self.center_y),
                    (self.center_x, self.center_y),
                ]
                Line(points=points, width=screen.dp(2))


class Explosion(SpriteWidget):
    """爆炸效果 - 图片动画版"""

    def __init__(self, pos, size_ratio=0.08, **kwargs):
        super().__init__(**kwargs)
        self.pos = pos
        self.size_hint = (None, None)
        self.set_size_rel(size_ratio, size_ratio)
        self.frame = 0
        self.max_frames = 7  # 7张爆炸图片

        # 加载爆炸图片序列
        self._image_loaded = False
        self._current_image = 0
        self.load_explosion_images()

    def load_explosion_images(self):
        """加载爆炸图片序列"""
        self.explosion_images = []
        for i in range(1, 8):
            path = get_resource_path(f'explosion/Explosion{i}.png')
            if os.path.exists(path):
                self.explosion_images.append(path)

        if self.explosion_images:
            self._image_loaded = self.setup_image(
                self.explosion_images[0],
                allow_stretch=True,
                keep_ratio=True
            )

    def draw_explosion(self):
        """更新爆炸动画"""
        if self._image_loaded and self.explosion_images:
            # 更新图片
            image_index = min(self.frame, len(self.explosion_images) - 1)
            if self._image_widget and image_index != self._current_image:
                self._current_image = image_index
                self._image_widget.source = self.explosion_images[image_index]
                self._image_widget.reload()
        else:
            # 使用绘制动画
            self.canvas.clear()
            progress = self.frame / self.max_frames
            radius = self.width / 2 * progress
            alpha = 1 - progress

            with self.canvas:
                # 外圈
                Color(1, 1, 0.8, alpha)
                Ellipse(pos=(self.center_x - radius, self.center_y - radius),
                       size=(radius * 2, radius * 2))
                # 中圈
                Color(1, 0.8, 0.2, alpha)
                radius2 = radius * 0.7
                Ellipse(pos=(self.center_x - radius2, self.center_y - radius2),
                       size=(radius2 * 2, radius2 * 2))
                # 内圈
                Color(1, 0.4, 0, alpha)
                radius3 = radius * 0.4
                Ellipse(pos=(self.center_x - radius3, self.center_y - radius3),
                       size=(radius3 * 2, radius3 * 2))


class GameWidget(FloatLayout):
    """游戏主界面 - 图片版"""
    score = NumericProperty(0)
    level = NumericProperty(1)
    lives = NumericProperty(3)
    bombs = NumericProperty(3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_state = 'menu'
        self.player = None
        self.enemies = []
        self.bullets = []
        self.powerups = []
        self.explosions = []
        self.boss = None
        self.boss_spawned = False

        # 触摸控制
        self.touch_pos = None
        self.touch_offset = (0, 0)
        self.last_tap_time = 0
        self.double_tap_threshold = 0.3

        # 计时器
        self.spawn_timer = 0
        self.shoot_timer = 0
        self.level_timer = 0

        # 关卡配置
        self.level_config = self.get_level_config()

        # 背景
        self.setup_background()

        # 初始化UI
        self.setup_ui()

        # 开始游戏循环
        Clock.schedule_interval(self.update, 1/60)

        # 监听屏幕尺寸变化
        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, instance, width, height):
        """窗口大小改变时重新适配"""
        global screen
        screen = ScreenAdapter()
        self.update_ui_positions()

    def setup_background(self):
        """设置背景"""
        bg_path = get_resource_path('plane_sprite/png/BG.png')
        if os.path.exists(bg_path):
            self.bg = Image(
                source=bg_path,
                allow_stretch=True,
                keep_ratio=False,
                size_hint=(1, 1),
                pos_hint={'x': 0, 'y': 0}
            )
            self.add_widget(self.bg)
        else:
            # 使用黑色背景
            with self.canvas.before:
                Color(0, 0, 0, 1)
                self.bg_rect = Rectangle(pos=(0, 0), size=Window.size)

    def get_level_config(self):
        """获取关卡配置"""
        configs = []
        for i in range(1, 11):
            configs.append({
                'level': i,
                'enemies_to_kill': 10 + i * 5,
                'spawn_rate': max(0.5, 2 - i * 0.1),
                'enemy_types': ['normal'] if i < 3 else ['normal', 'fast'] if i < 6 else ['normal', 'fast', 'tank'],
                'boss_health': 20 + i * 10,
            })
        return configs

    def setup_ui(self):
        """设置UI - 响应式布局"""
        # 分数标签
        self.score_label = Label(
            text='分数: 0',
            font_size=screen.sp(18),
            size_hint=(None, None),
            size=(screen.rel_x(0.35), screen.rel_y(0.04)),
            pos=(screen.dp(10), screen.real_height - screen.rel_y(0.06)),
            color=(1, 1, 1, 1),
            halign='left',
            valign='middle',
        )
        self.add_widget(self.score_label)

        # 关卡标签
        self.level_label = Label(
            text='关卡: 1',
            font_size=screen.sp(18),
            size_hint=(None, None),
            size=(screen.rel_x(0.35), screen.rel_y(0.04)),
            pos=(screen.real_width - screen.rel_x(0.35) - screen.dp(10),
                 screen.real_height - screen.rel_y(0.06)),
            color=(1, 1, 1, 1),
            halign='right',
            valign='middle',
        )
        self.add_widget(self.level_label)

        # 生命显示
        self.lives_label = Label(
            text='❤ x 3',
            font_size=screen.sp(16),
            size_hint=(None, None),
            size=(screen.rel_x(0.25), screen.rel_y(0.03)),
            pos=(screen.dp(10), screen.real_height - screen.rel_y(0.1)),
            color=(1, 0.5, 0.5, 1),
            halign='left',
        )
        self.add_widget(self.lives_label)

        # 炸弹显示
        self.bombs_label = Label(
            text='💣 x 3',
            font_size=screen.sp(16),
            size_hint=(None, None),
            size=(screen.rel_x(0.25), screen.rel_y(0.03)),
            pos=(screen.real_width - screen.rel_x(0.25) - screen.dp(10),
                 screen.real_height - screen.rel_y(0.1)),
            color=(0.7, 0.7, 0.7, 1),
            halign='right',
        )
        self.add_widget(self.bombs_label)

        # 开始菜单
        self.show_menu()

    def update_ui_positions(self):
        """更新UI位置"""
        if hasattr(self, 'score_label'):
            self.score_label.pos = (screen.dp(10), screen.real_height - screen.rel_y(0.06))
            self.score_label.size = (screen.rel_x(0.35), screen.rel_y(0.04))
            self.score_label.font_size = screen.sp(18)

        if hasattr(self, 'level_label'):
            self.level_label.pos = (screen.real_width - screen.rel_x(0.35) - screen.dp(10),
                                   screen.real_height - screen.rel_y(0.06))
            self.level_label.size = (screen.rel_x(0.35), screen.rel_y(0.04))
            self.level_label.font_size = screen.sp(18)

        if hasattr(self, 'lives_label'):
            self.lives_label.pos = (screen.dp(10), screen.real_height - screen.rel_y(0.1))
            self.lives_label.size = (screen.rel_x(0.25), screen.rel_y(0.03))
            self.lives_label.font_size = screen.sp(16)

        if hasattr(self, 'bombs_label'):
            self.bombs_label.pos = (screen.real_width - screen.rel_x(0.25) - screen.dp(10),
                                   screen.real_height - screen.rel_y(0.1))
            self.bombs_label.size = (screen.rel_x(0.25), screen.rel_y(0.03))
            self.bombs_label.font_size = screen.sp(16)

    def show_menu(self):
        """显示主菜单"""
        self.menu_widget = FloatLayout()

        # 标题
        title = Label(
            text='[size=48]飞机大战[/size]\n[size=24]Android版[/size]',
            markup=True,
            font_size=screen.sp(36),
            pos_hint={'center_x': 0.5, 'center_y': 0.65},
            color=(0.2, 1, 1, 1),
        )
        self.menu_widget.add_widget(title)

        # 开始按钮 - 响应式大小
        start_btn = Button(
            text='开始游戏',
            font_size=screen.sp(22),
            size_hint=(0.5, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            background_color=(0.2, 0.6, 1, 1),
        )
        start_btn.bind(on_press=self.start_game)
        self.menu_widget.add_widget(start_btn)

        # 说明
        instructions = Label(
            text='[size=16]触摸屏幕移动飞机\n自动射击\n双击使用炸弹[/size]',
            markup=True,
            font_size=screen.sp(14),
            pos_hint={'center_x': 0.5, 'center_y': 0.2},
            color=(0.8, 0.8, 0.8, 1),
        )
        self.menu_widget.add_widget(instructions)

        self.add_widget(self.menu_widget)

    def start_game(self, instance=None):
        """开始游戏"""
        self.remove_widget(self.menu_widget)
        self.game_state = 'playing'
        self.score = 0
        self.level = 1
        self.lives = 3
        self.bombs = 3
        self.enemies_killed = 0
        self.boss_spawned = False
        self.boss = None

        # 创建玩家
        self.player = Player()
        self.player.pos = (screen.real_width/2 - self.player.width/2,
                          screen.rel_y(0.12))
        self.add_widget(self.player)

        # 清空列表
        self.enemies = []
        self.bullets = []
        self.powerups = []
        self.explosions = []

    def update(self, dt):
        """游戏主循环"""
        if self.game_state != 'playing':
            return

        # 更新计时器
        self.spawn_timer += dt
        self.shoot_timer += dt
        self.level_timer += dt

        # 获取当前关卡配置
        config = self.level_config[min(self.level - 1, len(self.level_config) - 1)]

        # 生成敌机
        if self.spawn_timer >= config['spawn_rate'] and not self.boss_spawned:
            self.spawn_timer = 0
            self.spawn_enemy(config['enemy_types'])

        # 自动射击
        if self.shoot_timer >= 0.15:
            self.shoot_timer = 0
            self.player_shoot()

        # 更新玩家
        self.update_player(dt)

        # 更新敌机
        self.update_enemies(dt)

        # 更新子弹
        self.update_bullets(dt)

        # 更新道具
        self.update_powerups(dt)

        # 更新爆炸
        self.update_explosions(dt)

        # 更新Boss
        if self.boss:
            self.update_boss(dt)

        # 检查关卡进度
        self.check_level_progress(config)

        # 更新UI
        self.update_ui()

        # 绘制所有元素
        self.draw_all()

    def spawn_enemy(self, enemy_types):
        """生成敌机"""
        enemy_type = random.choice(enemy_types)
        enemy = Enemy(enemy_type=enemy_type)
        margin = screen.dp(20)
        enemy.pos = (random.randint(int(margin), int(screen.real_width - enemy.width - margin)),
                    screen.real_height)
        self.enemies.append(enemy)
        self.add_widget(enemy)

    def player_shoot(self):
        """玩家射击"""
        if not self.player:
            return

        bullet_offsets = {
            1: [0],
            2: [-0.02, 0.02],
            3: [-0.03, 0, 0.03]
        }

        weapon_level = min(self.player.weapon_level, 3)
        for offset in bullet_offsets.get(weapon_level, [0]):
            bullet = Bullet(is_player=True)
            bullet.pos = (self.player.center_x - bullet.width/2 + screen.rel_x(offset),
                         self.player.top)
            self.bullets.append(bullet)
            self.add_widget(bullet)

    def update_player(self, dt):
        """更新玩家"""
        if not self.player:
            return

        # 触摸移动
        if self.touch_pos:
            target_x = self.touch_pos[0] - self.touch_offset[0]
            target_y = self.touch_pos[1] - self.touch_offset[1]

            # 平滑移动
            dx = target_x - self.player.x
            dy = target_y - self.player.y

            move_speed = self.player.speed * 60 * dt
            if abs(dx) > move_speed:
                dx = move_speed if dx > 0 else -move_speed
            if abs(dy) > move_speed:
                dy = move_speed if dy > 0 else -move_speed

            self.player.x += dx
            self.player.y += dy

            # 边界限制
            self.player.x = max(0, min(screen.real_width - self.player.width, self.player.x))
            self.player.y = max(0, min(screen.real_height - self.player.height, self.player.y))

        # 更新护盾
        if self.player.shield:
            self.player.shield_time -= dt
            if self.player.shield_time <= 0:
                self.player.shield = False

        # 更新无敌
        if self.player.invincible:
            self.player.invincible_time -= dt
            if self.player.invincible_time <= 0:
                self.player.invincible = False

    def update_enemies(self, dt):
        """更新敌机"""
        for enemy in self.enemies[:]:
            enemy.y -= enemy.speed

            # 敌机射击
            if random.random() < 0.005:
                bullet = Bullet(is_player=False)
                bullet.pos = (enemy.center_x - bullet.width/2, enemy.y)
                self.bullets.append(bullet)
                self.add_widget(bullet)

            # 移除出界敌机
            if enemy.y < -enemy.height:
                self.enemies.remove(enemy)
                self.remove_widget(enemy)

    def update_bullets(self, dt):
        """更新子弹"""
        for bullet in self.bullets[:]:
            if bullet.is_player:
                bullet.y += bullet.speed
            else:
                bullet.y -= bullet.speed

            # 移除出界子弹
            if bullet.y > screen.real_height + bullet.height or bullet.y < -bullet.height:
                self.bullets.remove(bullet)
                self.remove_widget(bullet)
                continue

            # 碰撞检测
            if bullet.is_player:
                # 玩家子弹打敌机
                for enemy in self.enemies[:]:
                    if self.collide(bullet, enemy):
                        enemy.health -= 1
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                            self.remove_widget(bullet)

                        if enemy.health <= 0:
                            self.score += enemy.score
                            self.enemies_killed += 1
                            self.create_explosion(enemy.center, enemy.width)
                            self.enemies.remove(enemy)
                            self.remove_widget(enemy)

                            # 掉落道具
                            if random.random() < 0.15:
                                self.spawn_powerup(enemy.center)
                        break

                # 玩家子弹打Boss
                if self.boss and self.collide(bullet, self.boss):
                    self.boss.health -= 1
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                        self.remove_widget(bullet)

                    if self.boss.health <= 0:
                        self.score += self.boss.score
                        self.create_explosion(self.boss.center, self.boss.width * 1.5)
                        self.remove_widget(self.boss)
                        self.boss = None
                        self.boss_spawned = False
                        self.level += 1
                        self.enemies_killed = 0
            else:
                # 敌方子弹打玩家
                if self.player and self.collide(bullet, self.player):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                        self.remove_widget(bullet)

                    if not self.player.shield and not self.player.invincible:
                        self.player_hit()

    def update_powerups(self, dt):
        """更新道具"""
        for powerup in self.powerups[:]:
            powerup.y -= powerup.speed

            # 移除出界道具
            if powerup.y < -powerup.height:
                self.powerups.remove(powerup)
                self.remove_widget(powerup)
                continue

            # 碰撞检测
            if self.player and self.collide(powerup, self.player):
                self.apply_powerup(powerup.powerup_type)
                self.powerups.remove(powerup)
                self.remove_widget(powerup)

    def update_explosions(self, dt):
        """更新爆炸效果"""
        for explosion in self.explosions[:]:
            explosion.frame += 1
            if explosion.frame >= explosion.max_frames:
                self.explosions.remove(explosion)
                self.remove_widget(explosion)

    def update_boss(self, dt):
        """更新Boss"""
        if not self.boss:
            return

        # 移动
        self.boss.x += self.boss.speed * self.boss.direction
        if self.boss.x <= 0 or self.boss.x >= screen.real_width - self.boss.width:
            self.boss.direction *= -1

        # 射击
        self.boss.shoot_timer += dt
        if self.boss.shoot_timer >= 0.5:
            self.boss.shoot_timer = 0
            # 发射多颗子弹
            for i in range(3):
                bullet = Bullet(is_player=False)
                bullet.pos = (self.boss.x + self.boss.width * (0.15 + i * 0.35), self.boss.y)
                self.bullets.append(bullet)
                self.add_widget(bullet)

    def check_level_progress(self, config):
        """检查关卡进度"""
        if self.enemies_killed >= config['enemies_to_kill'] and not self.boss_spawned:
            self.spawn_boss()

    def spawn_boss(self):
        """生成Boss"""
        self.boss_spawned = True
        self.boss = Boss(level=self.level)
        self.boss.pos = (screen.real_width/2 - self.boss.width/2,
                        screen.real_height - self.boss.height - screen.dp(20))
        self.add_widget(self.boss)

        # 清除所有敌机
        for enemy in self.enemies:
            self.remove_widget(enemy)
        self.enemies = []

    def spawn_powerup(self, pos):
        """生成道具"""
        powerup_type = random.choice(['health', 'weapon', 'shield', 'bomb'])
        powerup = PowerUp(powerup_type=powerup_type)
        powerup.pos = (pos[0] - powerup.width/2, pos[1] - powerup.height/2)
        self.powerups.append(powerup)
        self.add_widget(powerup)

    def apply_powerup(self, powerup_type):
        """应用道具效果"""
        if powerup_type == 'health':
            self.lives = min(self.lives + 1, 5)
        elif powerup_type == 'weapon':
            self.player.weapon_level = min(self.player.weapon_level + 1, 3)
        elif powerup_type == 'shield':
            self.player.shield = True
            self.player.shield_time = 5
        elif powerup_type == 'bomb':
            self.bombs = min(self.bombs + 1, 5)

    def player_hit(self):
        """玩家被击中"""
        self.lives -= 1
        self.player.weapon_level = max(1, self.player.weapon_level - 1)
        self.player.invincible = True
        self.player.invincible_time = 2

        if self.lives <= 0:
            self.game_over()

    def use_bomb(self):
        """使用炸弹"""
        if self.bombs <= 0:
            return

        self.bombs -= 1

        # 清除所有敌机和子弹
        for enemy in self.enemies:
            self.score += enemy.score
            self.create_explosion(enemy.center, enemy.width)
            self.remove_widget(enemy)
        self.enemies = []

        for bullet in self.bullets[:]:
            if not bullet.is_player:
                self.bullets.remove(bullet)
                self.remove_widget(bullet)

        # 对Boss造成伤害
        if self.boss:
            self.boss.health -= 10
            if self.boss.health <= 0:
                self.score += self.boss.score
                self.create_explosion(self.boss.center, self.boss.width * 1.5)
                self.remove_widget(self.boss)
                self.boss = None
                self.boss_spawned = False
                self.level += 1
                self.enemies_killed = 0

    def create_explosion(self, pos, size):
        """创建爆炸效果"""
        size_ratio = size / screen.real_width
        explosion = Explosion(pos=(pos[0] - size/2, pos[1] - size/2), size_ratio=size_ratio)
        self.explosions.append(explosion)
        self.add_widget(explosion)

    def game_over(self):
        """游戏结束"""
        self.game_state = 'gameover'

        # 显示游戏结束界面
        gameover_widget = FloatLayout()

        # 半透明背景
        with gameover_widget.canvas:
            Color(0, 0, 0, 0.7)
            Rectangle(pos=(0, 0), size=(screen.real_width, screen.real_height))

        # 游戏结束文字
        title = Label(
            text='[size=48]游戏结束[/size]',
            markup=True,
            font_size=screen.sp(36),
            pos_hint={'center_x': 0.5, 'center_y': 0.65},
            color=(1, 0.3, 0.3, 1),
        )
        gameover_widget.add_widget(title)

        # 分数
        score_label = Label(
            text=f'[size=24]最终分数: {self.score}[/size]\n[size=20]到达关卡: {self.level}[/size]',
            markup=True,
            font_size=screen.sp(18),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            color=(1, 1, 1, 1),
        )
        gameover_widget.add_widget(score_label)

        # 重新开始按钮
        restart_btn = Button(
            text='重新开始',
            font_size=screen.sp(22),
            size_hint=(0.5, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.35},
            background_color=(0.2, 0.6, 1, 1),
        )
        restart_btn.bind(on_press=self.restart_game)
        gameover_widget.add_widget(restart_btn)

        self.add_widget(gameover_widget)
        self.gameover_widget = gameover_widget

    def restart_game(self, instance=None):
        """重新开始游戏"""
        if hasattr(self, 'gameover_widget'):
            self.remove_widget(self.gameover_widget)

        # 清理
        if self.player:
            self.remove_widget(self.player)
        for enemy in self.enemies:
            self.remove_widget(enemy)
        for bullet in self.bullets:
            self.remove_widget(bullet)
        for powerup in self.powerups:
            self.remove_widget(powerup)
        for explosion in self.explosions:
            self.remove_widget(explosion)
        if self.boss:
            self.remove_widget(self.boss)

        # 重新开始
        self.start_game()

    def collide(self, widget1, widget2):
        """碰撞检测"""
        return (widget1.x < widget2.right and
                widget1.right > widget2.x and
                widget1.y < widget2.top and
                widget1.top > widget2.y)

    def update_ui(self):
        """更新UI"""
        self.score_label.text = f'分数: {self.score}'
        self.level_label.text = f'关卡: {self.level}'
        self.lives_label.text = f'❤ x {self.lives}'
        self.bombs_label.text = f'💣 x {self.bombs}'

    def draw_all(self):
        """绘制所有元素"""
        if self.player:
            self.player.update_effects()

        for enemy in self.enemies:
            enemy.draw_ship()

        for bullet in self.bullets:
            bullet.draw_bullet()

        for powerup in self.powerups:
            powerup.draw_item()

        for explosion in self.explosions:
            explosion.draw_explosion()

        if self.boss:
            self.boss.draw_ship()

    # 触摸事件处理 - 优化版
    def on_touch_down(self, touch):
        if self.game_state != 'playing' or not self.player:
            return super().on_touch_down(touch)

        import time
        current_time = time.time()

        # 检测双击
        if current_time - self.last_tap_time < self.double_tap_threshold:
            self.use_bomb()
            self.last_tap_time = 0
            return True

        self.last_tap_time = current_time

        # 记录触摸位置和偏移
        self.touch_pos = touch.pos
        self.touch_offset = (touch.x - self.player.x, touch.y - self.player.y)

        return True

    def on_touch_move(self, touch):
        if self.game_state != 'playing' or not self.player:
            return super().on_touch_move(touch)

        self.touch_pos = touch.pos
        return True

    def on_touch_up(self, touch):
        self.touch_pos = None
        return super().on_touch_up(touch)


class PlaneWarApp(App):
    """飞机大战应用"""
    def build(self):
        # 全屏模式
        Window.fullscreen = 'auto'
        return GameWidget()


if __name__ == '__main__':
    PlaneWarApp().run()
