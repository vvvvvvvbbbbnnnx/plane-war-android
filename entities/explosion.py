# -*- coding: utf-8 -*-
"""
飞机大战 - 爆炸效果
"""
from typing import Optional, List
import os
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock

from core.entity import SpriteEntity
from utils.screen import screen
from utils.resources import ResourceManager


class Explosion(SpriteEntity):
    """
    爆炸效果

    使用帧动画或粒子效果显示爆炸
    """

    def __init__(self, pos: tuple = (0, 0), size_ratio: float = 0.08, **kwargs):
        """
        初始化爆炸效果

        Args:
            pos: 爆炸位置
            size_ratio: 大小比例
        """
        super().__init__(**kwargs)

        # 设置位置和大小
        self.pos = pos
        self.set_size_rel(size_ratio, size_ratio)

        # 动画帧
        self._frames: List[str] = []
        self._current_frame: int = 0
        self._max_frames: int = 15
        self._frame_duration: float = 0.05  # 每帧持续时间
        self._frame_timer: float = 0

        # 尝试加载爆炸动画帧
        self._load_frames()

        if self._frames:
            # 使用帧动画
            self.setup_image(self._frames[0])
            self._use_frames = True
        else:
            # 使用粒子绘制
            self._use_frames = False
            self._particle_phase = 0  # 0-1 粒子动画进度

    def _load_frames(self) -> None:
        """加载爆炸动画帧"""
        # 尝试加载 explosion_00.png 到 explosion_14.png
        for i in range(15):
            frame_name = f'explosion_{i:02d}.png'
            path = ResourceManager.get_image_path(frame_name)
            if path and os.path.exists(path):
                self._frames.append(path)

        # 也尝试加载 explosion/Explosion1.png 等格式
        if not self._frames:
            for i in range(1, 8):
                frame_name = f'explosion/Explosion{i}.png'
                path = ResourceManager.get_path(frame_name)
                if path and os.path.exists(path):
                    self._frames.append(path)

        self._max_frames = len(self._frames) if self._frames else 15

    def update(self, dt: float) -> None:
        """更新爆炸动画"""
        if not self.active:
            return

        self._frame_timer += dt

        if self._use_frames and self._frames:
            # 帧动画模式
            if self._frame_timer >= self._frame_duration:
                self._frame_timer = 0
                self._current_frame += 1

                if self._current_frame >= len(self._frames):
                    self.active = False
                else:
                    # 更新图片
                    if self._image_widget:
                        self._image_widget.source = self._frames[self._current_frame]
        else:
            # 粒子模式
            self._particle_phase += dt * 3  # 约0.33秒完成
            if self._particle_phase >= 1.0:
                self.active = False

    def draw(self) -> None:
        """绘制爆炸效果"""
        if self._use_frames:
            return

        # 粒子绘制模式
        self.canvas.clear()

        if self._particle_phase >= 1.0:
            return

        progress = self._particle_phase
        radius = self.width / 2 * progress
        alpha = 1 - progress

        with self.canvas:
            # 外圈（白色）
            Color(1, 1, 0.8, alpha)
            Ellipse(
                pos=(self.center_x - radius, self.center_y - radius),
                size=(radius * 2, radius * 2)
            )

            # 中圈（橙色）
            Color(1, 0.8, 0.2, alpha)
            radius2 = radius * 0.7
            Ellipse(
                pos=(self.center_x - radius2, self.center_y - radius2),
                size=(radius2 * 2, radius2 * 2)
            )

            # 内圈（红色）
            Color(1, 0.4, 0, alpha)
            radius3 = radius * 0.4
            Ellipse(
                pos=(self.center_x - radius3, self.center_y - radius3),
                size=(radius3 * 2, radius3 * 2)
            )

    def reset(self) -> None:
        """重置爆炸状态"""
        super().reset()
        self._current_frame = 0
        self._frame_timer = 0
        self._particle_phase = 0

        if self._frames:
            self._use_frames = True
            if self._image_widget:
                self._image_widget.source = self._frames[0]
