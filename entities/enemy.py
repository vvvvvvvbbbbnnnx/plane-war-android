# -*- coding: utf-8 -*-
"""
飞机大战 - 敌机
"""
from typing import Optional, List
import random
from kivy.properties import NumericProperty, StringProperty
from kivy.graphics import Color, Rectangle, Ellipse, Line

from core.entity import Entity
from config.settings import get_config
from utils.screen import screen
from utils.helpers import chance


class Enemy(Entity):
    """
    敌机

    Attributes:
        enemy_type: 敌机类型 ('normal', 'fast', 'tank')
        health: 当前生命值
        score: 击杀得分
    """

    enemy_type = StringProperty('normal')
    health = NumericProperty(1)
    score = NumericProperty(100)

    # 类型配置
    TYPE_CONFIGS = {
        'normal': {
            'width_ratio': 0.08,
            'height_ratio': 0.05,
            'health': 1,
            'speed': 3.0,
            'score': 100,
            'shoot_prob': 0.005,
            'color': (1, 0.2, 0.2),
        },
        'fast': {
            'width_ratio': 0.06,
            'height_ratio': 0.04,
            'health': 1,
            'speed': 5.0,
            'score': 150,
            'shoot_prob': 0.008,
            'color': (0.8, 0.4, 1),
        },
        'tank': {
            'width_ratio': 0.11,
            'height_ratio': 0.06,
            'health': 3,
            'speed': 2.0,
            'score': 300,
            'shoot_prob': 0.01,
            'color': (0.4, 0.4, 0.4),
        },
    }

    def __init__(self, enemy_type: str = 'normal', **kwargs):
        super().__init__(**kwargs)
        self.entity_type = 'enemy'
        self.enemy_type = enemy_type

        # 加载配置
        self._setup_type()

        # 尝试加载图片
        image_map = {
            'normal': 'enemy_normal.png',
            'fast': 'enemy_fast.png',
            'tank': 'enemy_tank.png',
        }
        self._image_loaded = self.setup_image(image_map.get(enemy_type, 'enemy_normal.png'))

        # 碰撞盒
        self._hitbox_scale = 0.8

    def _setup_type(self) -> None:
        """根据类型设置属性"""
        config = get_config()

        # 从配置获取参数
        if self.enemy_type in config.enemies:
            enemy_config = config.enemies[self.enemy_type]
            self.set_size_rel(enemy_config.width_ratio, enemy_config.height_ratio)
            self.health = enemy_config.health
            self._base_speed = enemy_config.speed
            self.score = enemy_config.score
            self._shoot_prob = enemy_config.shoot_probability
            self._color = (
                enemy_config.health / 3,  # 根据生命值设置颜色
                0.2 + (0.3 if self.enemy_type == 'fast' else 0),
                0.2 + (0.8 if self.enemy_type == 'tank' else 0),
            )
        else:
            # 使用默认配置
            type_config = self.TYPE_CONFIGS.get(self.enemy_type, self.TYPE_CONFIGS['normal'])
            self.set_size_rel(type_config['width_ratio'], type_config['height_ratio'])
            self.health = type_config['health']
            self._base_speed = type_config['speed']
            self.score = type_config['score']
            self._shoot_prob = type_config['shoot_prob']
            self._color = type_config['color']

        # 设置速度
        self.speed = screen.scale_value(self._base_speed)
        self.velocity_y = -self.speed

    def update(self, dt: float) -> None:
        """更新敌机"""
        super().update(dt)

        # 检查是否出界
        if self.y < -self.height * 2:
            self.active = False

    def should_shoot(self) -> bool:
        """
        检查是否应该射击

        Returns:
            是否射击
        """
        return chance(self._shoot_prob)

    def take_damage(self, amount: int = 1) -> bool:
        """受到伤害，生命归零时自动标记 inactive"""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.active = False
            return True
        return False

    def draw(self) -> None:
        """绘制敌机"""
        if self._image_loaded:
            return

        self.canvas.clear()
        w, h = self.size

        with self.canvas:
            Color(*self._color)

            if self.enemy_type == 'normal':
                # 普通敌机 - 菱形
                points = [
                    (self.center_x, self.y),
                    (self.x, self.top - h * 0.25),
                    (self.center_x, self.top - h * 0.5),
                    (self.right, self.top - h * 0.25),
                ]
                Line(points=points, width=screen.dp(2), close=True)

            elif self.enemy_type == 'fast':
                # 快速敌机 - 三角形
                points = [
                    (self.center_x, self.y),
                    (self.x, self.top),
                    (self.center_x, self.top - h * 0.25),
                    (self.right, self.top),
                ]
                Line(points=points, width=screen.dp(2), close=True)

            elif self.enemy_type == 'tank':
                # 坦克敌机 - 方形
                Rectangle(
                    pos=(self.x + w*0.1, self.y + h*0.1),
                    size=(w * 0.8, h * 0.8)
                )
                Color(0.6, 0.2, 0.2)
                Rectangle(
                    pos=(self.x + w*0.2, self.y + h*0.2),
                    size=(w * 0.6, h * 0.6)
                )

    def reset(self) -> None:
        """重置敌机状态"""
        super().reset()
        self._setup_type()
