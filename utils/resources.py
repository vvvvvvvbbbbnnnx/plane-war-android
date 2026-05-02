"""
飞机大战 - 资源管理器

统一管理游戏资源（图片、音效、字体等）的加载和缓存。
"""
import os
import sys
from typing import Any, Optional

from kivy.core.audio import SoundLoader
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_add_path, resource_find


class ResourceManager:
    """
    资源管理器（单例模式）

    提供资源路径查找、加载、缓存等功能。

    Attributes:
        base_path: 资源根目录
        image_cache: 图片缓存
        sound_cache: 音效缓存
    """

    _instance: Optional['ResourceManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 资源根目录
        self.base_path = self._find_base_path()

        # 添加资源路径
        self._add_resource_paths()

        # 缓存
        self._image_cache: dict[str, Any] = {}
        self._sound_cache: dict[str, Any] = {}
        self._loaded: bool = False

    def _find_base_path(self) -> str:
        """查找资源根目录"""
        # 尝试多种路径
        possible_paths = [
            os.path.dirname(os.path.abspath(__file__)),
            os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv else '',
            os.getcwd(),
            '.',
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                # 检查是否是项目根目录
                assets_path = os.path.join(path, 'assets')
                if os.path.exists(assets_path):
                    return path

        # 默认使用当前目录
        return os.getcwd()

    def _add_resource_paths(self) -> None:
        """添加资源搜索路径"""
        paths = [
            self.base_path,
            os.path.join(self.base_path, 'assets'),
            os.path.join(self.base_path, 'assets', 'images'),
            os.path.join(self.base_path, 'assets', 'sounds'),
            os.path.join(self.base_path, 'assets', 'fonts'),
        ]

        for path in paths:
            if os.path.exists(path):
                resource_add_path(path)

    def get_path(self, filename: str) -> Optional[str]:
        """
        获取资源文件的完整路径

        Args:
            filename: 文件名

        Returns:
            完整路径，如果找不到返回None
        """
        # 先用 Kivy 资源查找
        result = resource_find(filename)
        if result:
            return result

        # 尝试多种路径
        search_paths = [
            self.base_path,
            os.path.join(self.base_path, 'assets'),
            os.path.join(self.base_path, 'assets', 'images'),
            os.path.join(self.base_path, 'assets', 'sounds'),
            os.path.join(self.base_path, 'assets', 'fonts'),
        ]

        for base in search_paths:
            full_path = os.path.join(base, filename)
            if os.path.exists(full_path):
                return full_path

        return None

    @classmethod
    def exists(cls, filename: str) -> bool:
        """
        检查资源文件是否存在

        Args:
            filename: 文件名

        Returns:
            是否存在
        """
        instance = cls()
        return instance.get_path(filename) is not None

    @classmethod
    def load_image(cls, filename: str, cache: bool = True) -> Optional[CoreImage]:
        """
        加载图片

        Args:
            filename: 文件名
            cache: 是否缓存

        Returns:
            图片对象，加载失败返回None
        """
        instance = cls()

        # 检查缓存
        if cache and filename in instance._image_cache:
            return instance._image_cache[filename]

        # 获取路径
        path = instance.get_path(filename)
        if not path:
            return None

        try:
            image = CoreImage(path)
            if cache:
                instance._image_cache[filename] = image
            return image
        except Exception as e:
            print(f"[ResourceManager] 加载图片失败 {filename}: {e}")
            return None

    @classmethod
    def load_sound(cls, filename: str, cache: bool = True) -> Optional[Any]:
        """
        加载音效

        Args:
            filename: 文件名
            cache: 是否缓存

        Returns:
            音效对象，加载失败返回None
        """
        instance = cls()

        # 检查缓存
        if cache and filename in instance._sound_cache:
            return instance._sound_cache[filename]

        # 获取路径
        path = instance.get_path(filename)
        if not path:
            return None

        try:
            sound = SoundLoader.load(path)
            if cache and sound:
                instance._sound_cache[filename] = sound
            return sound
        except Exception as e:
            print(f"[ResourceManager] 加载音效失败 {filename}: {e}")
            return None

    @classmethod
    def get_image_path(cls, filename: str) -> Optional[str]:
        """获取图片路径"""
        instance = cls()
        return instance.get_path(os.path.join('images', filename))

    @classmethod
    def get_sound_path(cls, filename: str) -> Optional[str]:
        """获取音效路径"""
        instance = cls()
        return instance.get_path(os.path.join('sounds', filename))

    @classmethod
    def get_font_path(cls, filename: str) -> Optional[str]:
        """获取字体路径"""
        instance = cls()
        return instance.get_path(os.path.join('fonts', filename))

    def clear_cache(self) -> None:
        """清空缓存"""
        self._image_cache.clear()
        self._sound_cache.clear()

    def preload_common_resources(self) -> None:
        """预加载常用资源"""
        if self._loaded:
            return

        # 预加载常用图片
        common_images = [
            'player.png',
            'enemy_normal.png',
            'enemy_fast.png',
            'enemy_tank.png',
            'boss.png',
            'bullet_player.png',
            'bullet_enemy.png',
            'powerup_health.png',
            'powerup_weapon.png',
            'powerup_shield.png',
            'powerup_bomb.png',
            'background.png',
        ]

        for img in common_images:
            path = self.get_image_path(img)
            if path:
                self.load_image(path)

        self._loaded = True


# 全局资源管理器实例
resources = ResourceManager()


def get_resources() -> ResourceManager:
    """获取全局资源管理器实例"""
    return resources
