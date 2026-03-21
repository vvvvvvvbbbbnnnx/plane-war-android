# -*- coding: utf-8 -*-
"""
飞机大战 - Android版
使用 Kivy 框架，可打包为 APK
"""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Ellipse, Line, PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, BooleanProperty
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.metrics import dp
import random
import math

# 屏幕尺寸
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800


class Player(Widget):
    """玩家飞机"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (60, 80)
        self.pos = (SCREEN_WIDTH/2 - 30, 100)
        self.health = 3
        self.max_health = 3
        self.weapon_level = 1
        self.shield = False
        self.shield_time = 0
        self.invincible = False
        self.invincible_time = 0
        self.speed = 8

    def draw_ship(self):
        """绘制飞机"""
        self.canvas.clear()
        with self.canvas:
            # 主体
            Color(0.2, 1, 1, 1)
            body_points = [
                (self.center_x, self.top),
                (self.x + 10, self.y + 20),
                (self.x + 5, self.y),
                (self.right - 5, self.y),
                (self.right - 10, self.y + 20),
            ]
            Line(points=body_points, width=2, close=True)

            # 机翼
            Color(0.2, 0.6, 1, 1)
            left_wing = [
                (self.x + 10, self.y + 30),
                (self.x, self.y + 10),
                (self.x + 15, self.y + 20),
            ]
            right_wing = [
                (self.right - 10, self.y + 30),
                (self.right, self.y + 10),
                (self.right - 15, self.y + 20),
            ]
            Line(points=left_wing, width=2, close=True)
            Line(points=right_wing, width=2, close=True)

            # 驾驶舱
            Color(1, 1, 1, 1)
            Ellipse(pos=(self.center_x - 8, self.center_y - 5), size=(16, 25))

            # 护盾效果
            if self.shield:
                Color(0.2, 1, 1, 0.3)
                Ellipse(pos=(self.x - 10, self.y - 10),
                       size=(self.width + 20, self.height + 20))

            # 无敌闪烁
            if self.invincible and int(Clock.get_time() * 10) % 2:
                Color(1, 1, 1, 0.5)
                Rectangle(pos=self.pos, size=self.size)


class Enemy(Widget):
    """敌机基类"""
    enemy_type = 'normal'

    def __init__(self, enemy_type='normal', **kwargs):
        super().__init__(**kwargs)
        self.enemy_type = enemy_type
        self.setup_type()

    def setup_type(self):
        if self.enemy_type == 'normal':
            self.size = (40, 40)
            self.health = 1
            self.speed = 3
            self.score = 100
            self.color = (1, 0.2, 0.2)
        elif self.enemy_type == 'fast':
            self.size = (30, 35)
            self.health = 1
            self.speed = 5
            self.score = 150
            self.color = (0.8, 0.4, 1)
        elif self.enemy_type == 'tank':
            self.size = (55, 50)
            self.health = 3
            self.speed = 2
            self.score = 300
            self.color = (0.4, 0.4, 0.4)

    def draw_ship(self):
        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            if self.enemy_type == 'normal':
                points = [
                    (self.center_x, self.y),
                    (self.x, self.top - 10),
                    (self.center_x, self.top - 20),
                    (self.right, self.top - 10),
                ]
                Line(points=points, width=2, close=True)
            elif self.enemy_type == 'fast':
                points = [
                    (self.center_x, self.y),
                    (self.x, self.top),
                    (self.center_x, self.top - 10),
                    (self.right, self.top),
                ]
                Line(points=points, width=2, close=True)
            elif self.enemy_type == 'tank':
                Rectangle(pos=(self.x + 5, self.y + 5),
                         size=(self.width - 10, self.height - 10))
                Color(0.6, 0.2, 0.2)
                Rectangle(pos=(self.x + 10, self.y + 10),
                         size=(self.width - 20, self.height - 20))


class Boss(Widget):
    """Boss"""
    def __init__(self, level=1, **kwargs):
        super().__init__(**kwargs)
        self.level = level
        self.size = (120 + level * 10, 80 + level * 5)
        self.health = 20 + level * 10
        self.max_health = self.health
        self.speed = 1.5
        self.score = 1000 * level
        self.direction = 1
        self.shoot_timer = 0

    def draw_ship(self):
        self.canvas.clear()
        with self.canvas:
            # 主体
            Color(0.5, 0, 0)
            Ellipse(pos=self.pos, size=self.size)
            Color(0.8, 0.2, 0.2)
            Ellipse(pos=(self.x + 10, self.y + 5),
                   size=(self.width - 20, self.height - 10))

            # 核心
            Color(1, 0.84, 0)
            core_size = 30
            Ellipse(pos=(self.center_x - core_size/2, self.center_y - core_size/2),
                   size=(core_size, core_size))

            # 血条
            Color(0.3, 0.3, 0.3)
            bar_width = self.width
            bar_height = 8
            Rectangle(pos=(self.x, self.top + 5),
                     size=(bar_width, bar_height))
            Color(1, 0, 0)
            health_ratio = self.health / self.max_health
            Rectangle(pos=(self.x, self.top + 5),
                     size=(bar_width * health_ratio, bar_height))


class Bullet(Widget):
    """子弹"""
    def __init__(self, is_player=True, **kwargs):
        super().__init__(**kwargs)
        self.is_player = is_player
        if is_player:
            self.size = (8, 20)
            self.speed = 12
            self.color = (0.2, 1, 1)
        else:
            self.size = (10, 15)
            self.speed = 4
            self.color = (1, 0.3, 0.3)

    def draw_bullet(self):
        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            Ellipse(pos=self.pos, size=self.size)


class PowerUp(Widget):
    """道具"""
    powerup_type = 'health'

    def __init__(self, powerup_type='health', **kwargs):
        super().__init__(**kwargs)
        self.powerup_type = powerup_type
        self.size = (35, 35)
        self.speed = 2
        self.colors = {
            'health': (0.2, 1, 0.4),
            'weapon': (1, 1, 0.2),
            'shield': (0.2, 1, 1),
            'bomb': (0.5, 0.5, 0.5),
        }

    def draw_item(self):
        self.canvas.clear()
        with self.canvas:
            Color(*self.colors.get(self.powerup_type, (1, 1, 1)))
            Ellipse(pos=self.pos, size=self.size)

            if self.powerup_type == 'health':
                # 十字
                Color(1, 1, 1)
                Rectangle(pos=(self.center_x - 3, self.y + 5),
                         size=(6, self.height - 10))
                Rectangle(pos=(self.x + 5, self.center_y - 3),
                         size=(self.width - 10, 6))
            elif self.powerup_type == 'weapon':
                # 闪电
                Color(1, 0.84, 0)
                points = [
                    (self.center_x + 3, self.top - 3),
                    (self.x + 8, self.center_y),
                    (self.center_x, self.center_y),
                    (self.center_x - 3, self.y + 3),
                    (self.right - 8, self.center_y),
                    (self.center_x, self.center_y),
                ]
                Line(points=points, width=2)


class Explosion(Widget):
    """爆炸效果"""
    def __init__(self, pos, size=40, **kwargs):
        super().__init__(**kwargs)
        self.pos = pos
        self.size_hint = (None, None)
        self.size = (size, size)
        self.frame = 0
        self.max_frames = 15

    def draw_explosion(self):
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
    """游戏主界面"""
    score = NumericProperty(0)
    level = NumericProperty(1)
    lives = NumericProperty(3)
    bombs = NumericProperty(3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_state = 'menu'  # menu, playing, paused, gameover
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

        # 计时器
        self.spawn_timer = 0
        self.shoot_timer = 0
        self.level_timer = 0

        # 关卡配置
        self.level_config = self.get_level_config()

        # 初始化UI
        self.setup_ui()

        # 开始游戏循环
        Clock.schedule_interval(self.update, 1/60)

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
        """设置UI"""
        # 分数标签
        self.score_label = Label(
            text='分数: 0',
            font_size='20sp',
            pos_hint={'x': 0, 'top': 1},
            size_hint=(0.4, 0.05),
            color=(1, 1, 1, 1),
            halign='left',
            valign='middle',
        )
        self.add_widget(self.score_label)

        # 关卡标签
        self.level_label = Label(
            text='关卡: 1',
            font_size='20sp',
            pos_hint={'right': 1, 'top': 1},
            size_hint=(0.4, 0.05),
            color=(1, 1, 1, 1),
            halign='right',
            valign='middle',
        )
        self.add_widget(self.level_label)

        # 生命显示
        self.lives_label = Label(
            text='❤ x 3',
            font_size='18sp',
            pos_hint={'x': 0, 'top': 0.94},
            size_hint=(0.3, 0.04),
            color=(1, 0.5, 0.5, 1),
            halign='left',
        )
        self.add_widget(self.lives_label)

        # 炸弹显示
        self.bombs_label = Label(
            text='💣 x 3',
            font_size='18sp',
            pos_hint={'right': 1, 'top': 0.94},
            size_hint=(0.3, 0.04),
            color=(0.7, 0.7, 0.7, 1),
            halign='right',
        )
        self.add_widget(self.bombs_label)

        # 开始菜单
        self.show_menu()

    def show_menu(self):
        """显示主菜单"""
        self.menu_widget = FloatLayout()

        # 标题
        title = Label(
            text='[size=48]飞机大战[/size]\n[size=24]Android版[/size]',
            markup=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.65},
            color=(0.2, 1, 1, 1),
        )
        self.menu_widget.add_widget(title)

        # 开始按钮
        start_btn = Button(
            text='开始游戏',
            font_size='24sp',
            size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            background_color=(0.2, 0.6, 1, 1),
        )
        start_btn.bind(on_press=self.start_game)
        self.menu_widget.add_widget(start_btn)

        # 说明
        instructions = Label(
            text='[size=16]触摸屏幕移动飞机\n自动射击\n双击使用炸弹[/size]',
            markup=True,
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
        self.player.pos = (SCREEN_WIDTH/2 - 30, 100)
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
        enemy.pos = (random.randint(20, SCREEN_WIDTH - 60), SCREEN_HEIGHT)
        self.enemies.append(enemy)
        self.add_widget(enemy)

    def player_shoot(self):
        """玩家射击"""
        if not self.player:
            return

        # 根据武器等级发射不同数量的子弹
        if self.player.weapon_level == 1:
            bullet = Bullet(is_player=True)
            bullet.pos = (self.player.center_x - 4, self.player.top)
            self.bullets.append(bullet)
            self.add_widget(bullet)
        elif self.player.weapon_level == 2:
            for offset in [-10, 10]:
                bullet = Bullet(is_player=True)
                bullet.pos = (self.player.center_x - 4 + offset, self.player.top - 10)
                self.bullets.append(bullet)
                self.add_widget(bullet)
        else:
            for offset in [-15, 0, 15]:
                bullet = Bullet(is_player=True)
                bullet.pos = (self.player.center_x - 4 + offset, self.player.top - 10)
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
            self.player.x = max(0, min(SCREEN_WIDTH - self.player.width, self.player.x))
            self.player.y = max(0, min(SCREEN_HEIGHT - self.player.height, self.player.y))

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
                bullet.pos = (enemy.center_x - 5, enemy.y)
                self.bullets.append(bullet)
                self.add_widget(bullet)

            # 移除出界敌机
            if enemy.y < -50:
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
            if bullet.y > SCREEN_HEIGHT + 20 or bullet.y < -20:
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
            if powerup.y < -50:
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
        if self.boss.x <= 0 or self.boss.x >= SCREEN_WIDTH - self.boss.width:
            self.boss.direction *= -1

        # 射击
        self.boss.shoot_timer += dt
        if self.boss.shoot_timer >= 0.5:
            self.boss.shoot_timer = 0
            # 发射多颗子弹
            for i in range(3):
                bullet = Bullet(is_player=False)
                bullet.pos = (self.boss.x + 20 + i * 40, self.boss.y)
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
        self.boss.pos = (SCREEN_WIDTH/2 - self.boss.width/2, SCREEN_HEIGHT - 100)
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
        explosion = Explosion(pos=(pos[0] - size/2, pos[1] - size/2), size=size)
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
            Rectangle(pos=(0, 0), size=(SCREEN_WIDTH, SCREEN_HEIGHT))

        # 游戏结束文字
        title = Label(
            text='[size=48]游戏结束[/size]',
            markup=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.65},
            color=(1, 0.3, 0.3, 1),
        )
        gameover_widget.add_widget(title)

        # 分数
        score_label = Label(
            text=f'[size=24]最终分数: {self.score}[/size]\n[size=20]到达关卡: {self.level}[/size]',
            markup=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            color=(1, 1, 1, 1),
        )
        gameover_widget.add_widget(score_label)

        # 重新开始按钮
        restart_btn = Button(
            text='重新开始',
            font_size='24sp',
            size_hint=(0.5, 0.1),
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
            self.player.draw_ship()

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

    # 触摸事件处理
    def on_touch_down(self, touch):
        if self.game_state != 'playing' or not self.player:
            return super().on_touch_down(touch)

        # 检查是否双击（使用炸弹）
        if touch.is_double_tap:
            self.use_bomb()
            return True

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
        # 设置窗口大小
        Window.size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        return GameWidget()


if __name__ == '__main__':
    PlaneWarApp().run()
