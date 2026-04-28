# -*- coding: utf-8 -*-
"""
飞机大战 - 粒子系统

用于创建爆炸、尾迹等视觉效果
"""
from typing import List, Tuple, Optional
import random
import math
from kivy.graphics import Color, Point, PushMatrix, PopMatrix, Translate
from kivy.clock import Clock

from utils.screen import screen


class Particle:
    """
    单个粒子

    Attributes:
        x, y: 位置
        vx, vy: 速度
        lifetime: 生命周期
        max_lifetime: 最大生命周期
        color: 颜色 (r, g, b, a)
        size: 大小
    """

    def __init__(
        self,
        x: float, y: float,
        vx: float, vy: float,
        lifetime: float,
        color: Tuple[float, float, float, float],
        size: float
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.size = size
        self.active = True

    def update(self, dt: float) -> None:
        """
        更新粒子

        Args:
            dt: 时间增量
        """
        if not self.active:
            return

        # 更新位置
        self.x += self.vx * dt
        self.y += self.vy * dt

        # 更新生命周期
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False

    def get_alpha(self) -> float:
        """获取当前透明度"""
        return self.lifetime / self.max_lifetime


class ParticleSystem:
    """
    粒子系统

    管理大量粒子的创建、更新和渲染
    """

    def __init__(self, max_particles: int = 500):
        """
        初始化粒子系统

        Args:
            max_particles: 最大粒子数量
        """
        self.max_particles = max_particles
        self.particles: List[Particle] = []

        # 预定义效果
        self._effects = {
            'explosion': self._create_explosion_effect,
            'trail': self._create_trail_effect,
            'spark': self._create_spark_effect,
        }

    def emit(
        self,
        x: float, y: float,
        effect: str = 'explosion',
        count: int = 10,
        **kwargs
    ) -> None:
        """
        发射粒子

        Args:
            x, y: 发射位置
            effect: 效果类型
            count: 粒子数量
            **kwargs: 额外参数
        """
        if effect in self._effects:
            self._effects[effect](x, y, count, **kwargs)

    def _create_explosion_effect(
        self,
        x: float, y: float,
        count: int = 10,
        spread: float = 50,
        speed: float = 100,
        lifetime: float = 0.5,
        color: Tuple[float, float, float, float] = (1, 0.8, 0.2, 1)
    ) -> None:
        """创建爆炸效果"""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break

            angle = random.uniform(0, 2 * math.pi)
            speed_var = random.uniform(0.5, 1.5) * speed

            particle = Particle(
                x + random.uniform(-spread, spread) * 0.1,
                y + random.uniform(-spread, spread) * 0.1,
                math.cos(angle) * speed_var,
                math.sin(angle) * speed_var,
                lifetime * random.uniform(0.5, 1.5),
                color,
                random.uniform(2, 5)
            )
            self.particles.append(particle)

    def _create_trail_effect(
        self,
        x: float, y: float,
        count: int = 5,
        speed: float = 50,
        lifetime: float = 0.3,
        color: Tuple[float, float, float, float] = (0.2, 1, 1, 0.8)
    ) -> None:
        """创建尾迹效果"""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break

            particle = Particle(
                x + random.uniform(-5, 5),
                y + random.uniform(-5, 5),
                random.uniform(-speed * 0.2, speed * 0.2),
                -speed * random.uniform(0.5, 1.0),
                lifetime * random.uniform(0.5, 1.0),
                color,
                random.uniform(1, 3)
            )
            self.particles.append(particle)

    def _create_spark_effect(
        self,
        x: float, y: float,
        count: int = 8,
        spread: float = 20,
        speed: float = 80,
        lifetime: float = 0.2,
        color: Tuple[float, float, float, float] = (1, 1, 0.8, 1)
    ) -> None:
        """创建火花效果"""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break

            angle = random.uniform(0, 2 * math.pi)

            particle = Particle(
                x + random.uniform(-spread, spread),
                y + random.uniform(-spread, spread),
                math.cos(angle) * speed * random.uniform(0.3, 1.0),
                math.sin(angle) * speed * random.uniform(0.3, 1.0),
                lifetime * random.uniform(0.5, 1.5),
                color,
                random.uniform(1, 4)
            )
            self.particles.append(particle)

    def update(self, dt: float) -> None:
        """
        更新所有粒子

        Args:
            dt: 时间增量
        """
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.active:
                self.particles.remove(particle)

    def clear(self) -> None:
        """清空所有粒子"""
        self.particles.clear()

    def get_count(self) -> int:
        """获取粒子数量"""
        return len(self.particles)

    def get_particles(self) -> List[Particle]:
        """获取所有粒子"""
        return self.particles


# 全局粒子系统
particle_system = ParticleSystem()


def get_particles() -> ParticleSystem:
    """获取全局粒子系统"""
    return particle_system
