"""
飞机大战 - 音效管理器

管理游戏音效和背景音乐
"""
from typing import Any, Optional

from kivy.core.audio import SoundLoader


class AudioManager:
    """
    音效管理器（单例模式）

    Attributes:
        sounds: 音效缓存
        music_volume: 音乐音量
        sfx_volume: 音效音量
    """

    _instance: Optional['AudioManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 音效缓存
        self.sounds: dict[str, Any] = {}

        # 音量设置
        self.music_volume = 0.7
        self.sfx_volume = 0.8

        # 当前播放的音乐
        self.current_music: Optional[Any] = None
        self.current_music_name: Optional[str] = None

        # 是否启用
        self.enabled = True

    def load_sounds(self, sound_config: dict[str, str]) -> None:
        """
        加载音效

        Args:
            sound_config: {name: path} 音效配置
        """
        for name, path in sound_config.items():
                sound = SoundLoader.load(path)
                if sound:
                    self.sounds[name] = sound
                    print(f"[AudioManager] 加载音效: {name}")
                else:
                    print(f"[AudioManager] 加载失败: {name} ({path})")

    def play_sfx(self, name: str) -> None:
        """
        播放音效

        Args:
            name: 音效名称
        """
        if not self.enabled or name not in self.sounds:
            return

        sound = self.sounds[name]
        sound.volume = self.sfx_volume
        if sound.state == 'play':
            sound.stop()
        sound.play()

    def play_music(self, name: str, loop: bool = True) -> None:
        """
        播放背景音乐

        Args:
            name: 音乐名称
            loop: 是否循环
        """
        if not self.enabled or name not in self.sounds:
            return

        # 停止当前音乐
        if self.current_music:
            self.current_music.stop()

        # 播放新音乐
        self.current_music = self.sounds[name]
        self.current_music_name = name
        self.current_music.volume = self.music_volume
        self.current_music.loop = loop
        self.current_music.play()

    def stop_music(self) -> None:
        """停止背景音乐"""
        if self.current_music:
            self.current_music.stop()
            self.current_music = None
            self.current_music_name = None

    def pause_music(self) -> None:
        """暂停背景音乐"""
        if self.current_music:
            self.current_music.stop()

    def resume_music(self) -> None:
        """恢复背景音乐"""
        if self.current_music and self.current_music_name:
            self.current_music.play()

    def set_music_volume(self, volume: float) -> None:
        """
        设置音乐音量

        Args:
            volume: 音量 (0-1)
        """
        self.music_volume = max(0, min(1, volume))
        if self.current_music:
            self.current_music.volume = self.music_volume

    def set_sfx_volume(self, volume: float) -> None:
        """
        设置音效音量

        Args:
            volume: 音量 (0-1)
        """
        self.sfx_volume = max(0, min(1, volume))

    def toggle_enabled(self) -> bool:
        """
        切换音效开关

        Returns:
            切换后的状态
        """
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_music()
        return self.enabled

    def dispose(self) -> None:
        """清理资源"""
        self.stop_music()
        for sound in self.sounds.values():
            if hasattr(sound, 'stop'):
                sound.stop()
        self.sounds.clear()


# 全局音效管理器
audio_manager = AudioManager()


def get_audio() -> AudioManager:
    """获取全局音效管理器"""
    return audio_manager
