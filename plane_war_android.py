# -*- coding: utf-8 -*-
"""
飞机大战 - Android版 (响应式布局 + 图片素材版)
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
from kivy.properties import NumericProperty, StringProperty
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.resources import resource_add_path, resource_find
import random
import os

# 确保 Kivy 能找到资源（Android 兼容）
_dir = os.path.dirname(os.path.abspath(__file__))
resource_add_path(_dir)


def get_asset_path(filename):
    """获取资源文件的正确路径（Android 兼容）"""
    # 先用 Kivy 资源查找
    result = resource_find(filename)
    if result:
        return result
    # 再用绝对路径
    abs_path = os.path.join(_dir, filename)
    if os.path.exists(abs_path):
        return abs_path
    return None


class ScreenAdapter:
    """屏幕适配器"""
    DESIGN_WIDTH = 720
    DESIGN_HEIGHT = 1280
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
        self.real_width = Window.width
        self.real_height = Window.height
        self.scale_x = self.real_width / self.DESIGN_WIDTH
        self.scale_y = self.real_height / self.DESIGN_HEIGHT
        self.scale = max(self.MIN_SCALE, min(self.MAX_SCALE, min(self.scale_x, self.scale_y)))
        self.is_mobile = platform in ('android', 'ios')
        print(f"[ScreenAdapter] {self.real_width}x{self.real_height}, scale={self.scale:.2f}")

    def dp(self, value): return dp(value) * self.scale
    def sp(self, value): return sp(value) * self.scale
    def rel_w(self, ratio): return self.real_width * ratio
    def rel_h(self, ratio): return self.real_height * ratio


screen = ScreenAdapter()


class SpriteWidget(Widget):
    """精灵组件基类 - 支持图片和线条两种模式"""

    def __init__(self, image_source=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.image_source = image_source
        self.image_widget = None
        self.use_image = False

        # 尝试加载图片
        if image_source:
            asset_path = get_asset_path(image_source)
            if asset_path:
                self.image_widget = Image(source=asset_path, size=self.size, pos=self.pos,
                                         allow_stretch=True, keep_ratio=True)
                self.use_image = True

    def set_size_rel(self, w_ratio, h_ratio):
        self.size = (screen.rel_w(w_ratio), screen.rel_h(h_ratio))
        if self.image_widget:
            self.image_widget.size = self.size

    def update_position(self):
        if self.image_widget:
            self.image_widget.pos = self.pos

    def add_to_parent(self, parent):
        """添加到父组件"""
        if self.use_image and self.image_widget:
            parent.add_widget(self.image_widget)
        parent.add_widget(self)

    def remove_from_parent(self, parent):
        """从父组件移除"""
        if self.use_image and self.image_widget:
            parent.remove_widget(self.image_widget)
        parent.remove_widget(self)


class Player(SpriteWidget):
    """玩家飞机"""
    def __init__(self, **kwargs):
        super().__init__(image_source='player.png', **kwargs)
        self.set_size_rel(0.12, 0.08)
        self.health = 3
        self.max_health = 3
        self.weapon_level = 1
        self.shield = False
        self.shield_time = 0
        self.invincible = False
        self.invincible_time = 0
        self.speed = screen.scale * 8

    def draw_ship(self):
        """绘制飞机 - 图片模式或线条模式"""
        if self.use_image:
            self.update_position()
            # 无敌闪烁效果
            if self.invincible:
                self.image_widget.opacity = 0.5 if int(Clock.get_time() * 10) % 2 else 1.0
            else:
                self.image_widget.opacity = 1.0
            return

        # 线条绘制模式
        self.canvas.clear()
        with self.canvas:
            w, h = self.size
            # 主体
            Color(0.2, 1, 1, 1)
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

            # 无敌闪烁
            if self.invincible and int(Clock.get_time() * 10) % 2:
                Color(1, 1, 1, 0.5)
                Rectangle(pos=self.pos, size=self.size)


class Enemy(SpriteWidget):
    """敌机"""
    enemy_type = StringProperty('normal')

    def __init__(self, enemy_type='normal', **kwargs):
        source_map = {
            'normal': 'enemy_normal.png',
            'fast': 'enemy_fast.png',
            'tank': 'enemy_tank.png'
        }
        super().__init__(image_source=source_map.get(enemy_type), **kwargs)
        self.enemy_type = enemy_type
        self.setup_type()

    def setup_type(self):
        if self.enemy_type == 'normal':
            self.set_size_rel(0.08, 0.05)
            self.health = 1
            self.speed = screen.scale * 3
            self.score = 100
            self.color = (1, 0.2, 0.2)
        elif self.enemy_type == 'fast':
            self.set_size_rel(0.06, 0.04)
            self.health = 1
            self.speed = screen.scale * 5
            self.score = 150
            self.color = (0.8, 0.4, 1)
        elif self.enemy_type == 'tank':
            self.set_size_rel(0.11, 0.06)
            self.health = 3
            self.speed = screen.scale * 2
            self.score = 300
            self.color = (0.4, 0.4, 0.4)

    def draw_ship(self):
        if self.use_image:
            self.update_position()
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
    """Boss"""
    def __init__(self, level=1, **kwargs):
        super().__init__(image_source='boss.png', **kwargs)
        self.level = level
        base_w = 0.25 + level * 0.02
        base_h = 0.1 + level * 0.01
        self.set_size_rel(min(base_w, 0.4), min(base_h, 0.15))
        self.health = 20 + level * 10
        self.max_health = self.health
        self.speed = screen.scale * 1.5
        self.score = 1000 * level
        self.direction = 1
        self.shoot_timer = 0

    def draw_ship(self):
        if self.use_image:
            self.update_position()
            return

        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            Color(0.5, 0, 0)
            Ellipse(pos=self.pos, size=self.size)
            Color(0.8, 0.2, 0.2)
            Ellipse(pos=(self.x + w*0.08, self.y + h*0.06),
                   size=(w * 0.84, h * 0.88))
            Color(1, 0.84, 0)
            core_size = min(w, h) * 0.3
            Ellipse(pos=(self.center_x - core_size/2, self.center_y - core_size/2),
                   size=(core_size, core_size))


class Bullet(SpriteWidget):
    """子弹"""
    def __init__(self, is_player=True, **kwargs):
        source = 'bullet_player.png' if is_player else 'bullet_enemy.png'
        super().__init__(image_source=source, **kwargs)
        self.is_player = is_player
        if is_player:
            self.set_size_rel(0.02, 0.03)
            self.speed = screen.scale * 12
            self.color = (0.2, 1, 1)
        else:
            self.set_size_rel(0.025, 0.025)
            self.speed = screen.scale * 4
            self.color = (1, 0.3, 0.3)

    def draw_bullet(self):
        if self.use_image:
            self.update_position()
            return

        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            Ellipse(pos=self.pos, size=self.size)


class PowerUp(SpriteWidget):
    """道具"""
    def __init__(self, powerup_type='health', **kwargs):
        source_map = {
            'health': 'powerup_health.png',
            'weapon': 'powerup_weapon.png',
            'shield': 'powerup_shield.png',
            'bomb': 'powerup_bomb.png'
        }
        super().__init__(image_source=source_map.get(powerup_type), **kwargs)
        self.powerup_type = powerup_type
        self.set_size_rel(0.07, 0.04)
        self.speed = screen.scale * 2
        self.colors = {
            'health': (0.2, 1, 0.4),
            'weapon': (1, 1, 0.2),
            'shield': (0.2, 1, 1),
            'bomb': (0.5, 0.5, 0.5),
        }

    def draw_item(self):
        if self.use_image:
            self.update_position()
            return

        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            Color(*self.colors.get(self.powerup_type, (1, 1, 1)))
            Ellipse(pos=self.pos, size=self.size)


class Explosion(Widget):
    """爆炸效果"""
    def __init__(self, pos, size_ratio=0.08, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (screen.rel_w(size_ratio), screen.rel_h(size_ratio))
        self.pos = pos
        self.frame = 0
        self.max_frames = 15
        self.image_widget = None

        # 尝试加载爆炸动画帧
        frame_path = get_asset_path('explosion_00.png')
        if frame_path:
            self.image_widget = Image(source=frame_path, size=self.size, pos=self.pos,
                                       allow_stretch=True, keep_ratio=True)

    def update_frame(self):
        self.frame += 1
        if self.frame < self.max_frames and self.image_widget:
            frame_path = get_asset_path(f'explosion_{self.frame:02d}.png')
            if frame_path:
                self.image_widget.source = frame_path
                return True
        return False


class Background(Image):
    """滚动背景"""
    def __init__(self, **kwargs):
        bg_path = get_asset_path('background.png')
        if bg_path:
            super().__init__(source=bg_path, **kwargs)
        else:
            super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (screen.real_width, screen.real_height * 2)
        self.pos = (0, -screen.real_height)
        self.allow_stretch = True
        self.scroll_speed = screen.scale * 1

    def update(self, dt):
        self.y -= self.scroll_speed
        if self.y <= -screen.real_height:
            self.y = 0


class GameWidget(FloatLayout):
    """游戏主界面"""
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
        self.touch_pos = None
        self.touch_offset = (0, 0)
        self.last_tap_time = 0
        self.spawn_timer = 0
        self.shoot_timer = 0
        self.level_config = self.get_level_config()
        self.setup_ui()
        Clock.schedule_interval(self.update, 1/60)
        Window.bind(on_resize=self.on_window_resize)

    def on_window_resize(self, instance, width, height):
        global screen
        screen = ScreenAdapter()

    def get_level_config(self):
        configs = []
        for i in range(1, 11):
            configs.append({
                'level': i,
                'enemies_to_kill': 10 + i * 5,
                'spawn_rate': max(0.5, 2 - i * 0.1),
                'enemy_types': ['normal'] if i < 3 else ['normal', 'fast'] if i < 6 else ['normal', 'fast', 'tank'],
            })
        return configs

    def setup_ui(self):
        # 背景
        self.bg1 = Background()
        self.add_widget(self.bg1)

        # UI 标签
        self.score_label = Label(
            text='分数: 0', font_size=screen.sp(18),
            size_hint=(None, None), size=(screen.rel_w(0.35), screen.rel_h(0.04)),
            pos=(screen.dp(10), screen.real_height - screen.rel_h(0.06)),
            color=(1, 1, 1, 1), halign='left', valign='middle',
        )
        self.add_widget(self.score_label)

        self.level_label = Label(
            text='关卡: 1', font_size=screen.sp(18),
            size_hint=(None, None), size=(screen.rel_w(0.35), screen.rel_h(0.04)),
            pos=(screen.real_width - screen.rel_w(0.35) - screen.dp(10), screen.real_height - screen.rel_h(0.06)),
            color=(1, 1, 1, 1), halign='right', valign='middle',
        )
        self.add_widget(self.level_label)

        self.lives_label = Label(
            text='❤ x 3', font_size=screen.sp(16),
            size_hint=(None, None), size=(screen.rel_w(0.25), screen.rel_h(0.03)),
            pos=(screen.dp(10), screen.real_height - screen.rel_h(0.1)),
            color=(1, 0.5, 0.5, 1), halign='left',
        )
        self.add_widget(self.lives_label)

        self.bombs_label = Label(
            text='💣 x 3', font_size=screen.sp(16),
            size_hint=(None, None), size=(screen.rel_w(0.25), screen.rel_h(0.03)),
            pos=(screen.real_width - screen.rel_w(0.25) - screen.dp(10), screen.real_height - screen.rel_h(0.1)),
            color=(0.7, 0.7, 0.7, 1), halign='right',
        )
        self.add_widget(self.bombs_label)

        self.show_menu()

    def show_menu(self):
        self.menu_widget = FloatLayout()
        title = Label(
            text='[size=48]飞机大战[/size]\n[size=24]Android版[/size]',
            markup=True, font_size=screen.sp(36),
            pos_hint={'center_x': 0.5, 'center_y': 0.65},
            color=(0.2, 1, 1, 1),
        )
        self.menu_widget.add_widget(title)

        start_btn = Button(
            text='开始游戏', font_size=screen.sp(22),
            size_hint=(0.5, 0.08), pos_hint={'center_x': 0.5, 'center_y': 0.4},
            background_color=(0.2, 0.6, 1, 1),
        )
        start_btn.bind(on_press=self.start_game)
        self.menu_widget.add_widget(start_btn)

        instructions = Label(
            text='[size=16]触摸屏幕移动飞机\n自动射击\n双击使用炸弹[/size]',
            markup=True, font_size=screen.sp(14),
            pos_hint={'center_x': 0.5, 'center_y': 0.2},
            color=(0.8, 0.8, 0.8, 1),
        )
        self.menu_widget.add_widget(instructions)
        self.add_widget(self.menu_widget)

    def start_game(self, instance=None):
        self.remove_widget(self.menu_widget)
        self.game_state = 'playing'
        self.score = 0
        self.level = 1
        self.lives = 3
        self.bombs = 3
        self.enemies_killed = 0
        self.boss_spawned = False
        self.boss = None

        self.player = Player()
        self.player.pos = (screen.real_width/2 - self.player.width/2, screen.rel_h(0.12))
        self.player.add_to_parent(self)

        self.enemies = []
        self.bullets = []
        self.powerups = []
        self.explosions = []

    def update(self, dt):
        if self.game_state != 'playing':
            return

        self.bg1.update(dt)
        self.spawn_timer += dt
        self.shoot_timer += dt

        config = self.level_config[min(self.level - 1, len(self.level_config) - 1)]

        if self.spawn_timer >= config['spawn_rate'] and not self.boss_spawned:
            self.spawn_timer = 0
            self.spawn_enemy(config['enemy_types'])

        if self.shoot_timer >= 0.15:
            self.shoot_timer = 0
            self.player_shoot()

        self.update_player(dt)
        self.update_enemies(dt)
        self.update_bullets(dt)
        self.update_powerups(dt)
        self.update_explosions(dt)

        if self.boss:
            self.update_boss(dt)

        self.check_level_progress(config)
        self.update_ui()
        self.draw_all()

    def spawn_enemy(self, enemy_types):
        enemy_type = random.choice(enemy_types)
        enemy = Enemy(enemy_type=enemy_type)
        margin = screen.dp(20)
        enemy.pos = (random.randint(int(margin), int(screen.real_width - enemy.width - margin)), screen.real_height)
        self.enemies.append(enemy)
        enemy.add_to_parent(self)

    def player_shoot(self):
        if not self.player:
            return
        offsets = {1: [0], 2: [-0.02, 0.02], 3: [-0.03, 0, 0.03]}
        for offset in offsets.get(min(self.player.weapon_level, 3), [0]):
            bullet = Bullet(is_player=True)
            bullet.pos = (self.player.center_x - bullet.width/2 + screen.rel_w(offset), self.player.top)
            self.bullets.append(bullet)
            bullet.add_to_parent(self)

    def update_player(self, dt):
        if not self.player:
            return
        if self.touch_pos:
            target_x = self.touch_pos[0] - self.touch_offset[0]
            target_y = self.touch_pos[1] - self.touch_offset[1]
            dx = target_x - self.player.x
            dy = target_y - self.player.y
            move_speed = self.player.speed * 60 * dt
            if abs(dx) > move_speed: dx = move_speed if dx > 0 else -move_speed
            if abs(dy) > move_speed: dy = move_speed if dy > 0 else -move_speed
            self.player.x += dx
            self.player.y += dy
            self.player.x = max(0, min(screen.real_width - self.player.width, self.player.x))
            self.player.y = max(0, min(screen.real_height - self.player.height, self.player.y))

        if self.player.shield:
            self.player.shield_time -= dt
            if self.player.shield_time <= 0:
                self.player.shield = False

        if self.player.invincible:
            self.player.invincible_time -= dt
            if self.player.invincible_time <= 0:
                self.player.invincible = False

    def update_enemies(self, dt):
        for enemy in self.enemies[:]:
            enemy.y -= enemy.speed
            if random.random() < 0.005:
                bullet = Bullet(is_player=False)
                bullet.pos = (enemy.center_x - bullet.width/2, enemy.y)
                self.bullets.append(bullet)
                bullet.add_to_parent(self)
            if enemy.y < -enemy.height:
                self.enemies.remove(enemy)
                enemy.remove_from_parent(self)

    def update_bullets(self, dt):
        for bullet in self.bullets[:]:
            if bullet.is_player:
                bullet.y += bullet.speed
            else:
                bullet.y -= bullet.speed

            if bullet.y > screen.real_height + bullet.height or bullet.y < -bullet.height:
                self.bullets.remove(bullet)
                bullet.remove_from_parent(self)
                continue

            if bullet.is_player:
                for enemy in self.enemies[:]:
                    if self.collide(bullet, enemy):
                        enemy.health -= 1
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                            bullet.remove_from_parent(self)
                        if enemy.health <= 0:
                            self.score += enemy.score
                            self.enemies_killed += 1
                            self.create_explosion(enemy.center, enemy.width)
                            self.enemies.remove(enemy)
                            enemy.remove_from_parent(self)
                            if random.random() < 0.15:
                                self.spawn_powerup(enemy.center)
                        break

                if self.boss and self.collide(bullet, self.boss):
                    self.boss.health -= 1
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                        bullet.remove_from_parent(self)
                    if self.boss.health <= 0:
                        self.score += self.boss.score
                        self.create_explosion(self.boss.center, self.boss.width * 1.5)
                        self.boss.remove_from_parent(self)
                        self.boss = None
                        self.boss_spawned = False
                        self.level += 1
                        self.enemies_killed = 0
            else:
                if self.player and self.collide(bullet, self.player):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                        bullet.remove_from_parent(self)
                    if not self.player.shield and not self.player.invincible:
                        self.player_hit()

    def update_powerups(self, dt):
        for powerup in self.powerups[:]:
            powerup.y -= powerup.speed
            if powerup.y < -powerup.height:
                self.powerups.remove(powerup)
                powerup.remove_from_parent(self)
                continue
            if self.player and self.collide(powerup, self.player):
                self.apply_powerup(powerup.powerup_type)
                self.powerups.remove(powerup)
                powerup.remove_from_parent(self)

    def update_explosions(self, dt):
        for explosion in self.explosions[:]:
            if not explosion.update_frame():
                self.explosions.remove(explosion)
                self.remove_widget(explosion)

    def update_boss(self, dt):
        if not self.boss:
            return
        self.boss.x += self.boss.speed * self.boss.direction
        if self.boss.x <= 0 or self.boss.x >= screen.real_width - self.boss.width:
            self.boss.direction *= -1
        self.boss.shoot_timer += dt
        if self.boss.shoot_timer >= 0.5:
            self.boss.shoot_timer = 0
            for i in range(3):
                bullet = Bullet(is_player=False)
                bullet.pos = (self.boss.x + self.boss.width * (0.15 + i * 0.35), self.boss.y)
                self.bullets.append(bullet)
                bullet.add_to_parent(self)

    def check_level_progress(self, config):
        if self.enemies_killed >= config['enemies_to_kill'] and not self.boss_spawned:
            self.spawn_boss()

    def spawn_boss(self):
        self.boss_spawned = True
        self.boss = Boss(level=self.level)
        self.boss.pos = (screen.real_width/2 - self.boss.width/2, screen.real_height - self.boss.height - screen.dp(20))
        self.boss.add_to_parent(self)
        for enemy in self.enemies:
            enemy.remove_from_parent(self)
        self.enemies = []

    def spawn_powerup(self, pos):
        powerup_type = random.choice(['health', 'weapon', 'shield', 'bomb'])
        powerup = PowerUp(powerup_type=powerup_type)
        powerup.pos = (pos[0] - powerup.width/2, pos[1] - powerup.height/2)
        self.powerups.append(powerup)
        powerup.add_to_parent(self)

    def apply_powerup(self, powerup_type):
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
        self.lives -= 1
        self.player.weapon_level = max(1, self.player.weapon_level - 1)
        self.player.invincible = True
        self.player.invincible_time = 2
        if self.lives <= 0:
            self.game_over()

    def use_bomb(self):
        if self.bombs <= 0:
            return
        self.bombs -= 1
        for enemy in self.enemies:
            self.score += enemy.score
            self.create_explosion(enemy.center, enemy.width)
            enemy.remove_from_parent(self)
        self.enemies = []
        for bullet in self.bullets[:]:
            if not bullet.is_player:
                self.bullets.remove(bullet)
                bullet.remove_from_parent(self)
        if self.boss:
            self.boss.health -= 10
            if self.boss.health <= 0:
                self.score += self.boss.score
                self.create_explosion(self.boss.center, self.boss.width * 1.5)
                self.boss.remove_from_parent(self)
                self.boss = None
                self.boss_spawned = False
                self.level += 1
                self.enemies_killed = 0

    def create_explosion(self, pos, size):
        size_ratio = size / screen.real_width
        explosion = Explosion(pos=(pos[0] - size/2, pos[1] - size/2), size_ratio=size_ratio)
        self.explosions.append(explosion)
        self.add_widget(explosion)

    def game_over(self):
        self.game_state = 'gameover'
        gameover_widget = FloatLayout()
        with gameover_widget.canvas:
            Color(0, 0, 0, 0.7)
            Rectangle(pos=(0, 0), size=(screen.real_width, screen.real_height))
        title = Label(text='[size=48]游戏结束[/size]', markup=True, font_size=screen.sp(36),
                     pos_hint={'center_x': 0.5, 'center_y': 0.65}, color=(1, 0.3, 0.3, 1))
        gameover_widget.add_widget(title)
        score_label = Label(text=f'[size=24]最终分数: {self.score}[/size]\n[size=20]到达关卡: {self.level}[/size]',
                           markup=True, font_size=screen.sp(18), pos_hint={'center_x': 0.5, 'center_y': 0.5},
                           color=(1, 1, 1, 1))
        gameover_widget.add_widget(score_label)
        restart_btn = Button(text='重新开始', font_size=screen.sp(22), size_hint=(0.5, 0.08),
                            pos_hint={'center_x': 0.5, 'center_y': 0.35}, background_color=(0.2, 0.6, 1, 1))
        restart_btn.bind(on_press=self.restart_game)
        gameover_widget.add_widget(restart_btn)
        self.add_widget(gameover_widget)
        self.gameover_widget = gameover_widget

    def restart_game(self, instance=None):
        if hasattr(self, 'gameover_widget'):
            self.remove_widget(self.gameover_widget)
        if self.player:
            self.player.remove_from_parent(self)
        for enemy in self.enemies:
            enemy.remove_from_parent(self)
        for bullet in self.bullets:
            bullet.remove_from_parent(self)
        for powerup in self.powerups:
            powerup.remove_from_parent(self)
        for explosion in self.explosions:
            self.remove_widget(explosion)
        if self.boss:
            self.boss.remove_from_parent(self)
        self.start_game()

    def collide(self, w1, w2):
        return (w1.x < w2.right and w1.right > w2.x and w1.y < w2.top and w1.top > w2.y)

    def update_ui(self):
        self.score_label.text = f'分数: {self.score}'
        self.level_label.text = f'关卡: {self.level}'
        self.lives_label.text = f'❤ x {self.lives}'
        self.bombs_label.text = f'💣 x {self.bombs}'

    def draw_all(self):
        if self.player:
            self.player.draw_ship()
        for enemy in self.enemies:
            enemy.draw_ship()
        for bullet in self.bullets:
            bullet.draw_bullet()
        for powerup in self.powerups:
            powerup.draw_item()

    def on_touch_down(self, touch):
        if self.game_state != 'playing' or not self.player:
            return super().on_touch_down(touch)
        import time
        current_time = time.time()
        if current_time - self.last_tap_time < 0.3:
            self.use_bomb()
            self.last_tap_time = 0
            return True
        self.last_tap_time = current_time
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
    def build(self):
        Window.fullscreen = 'auto'
        return GameWidget()


if __name__ == '__main__':
    PlaneWarApp().run()
