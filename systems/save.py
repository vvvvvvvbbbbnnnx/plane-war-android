# -*- coding: utf-8 -*-
"""
飞机大战 - 存档系统

管理游戏存档和设置
"""
from typing import Dict, Any, Optional
from kivy.storage.jsonstore import JsonStore


class SaveManager:
    """
    存档管理器

    Attributes:
        store: JSON存储
    """

    def __init__(self, filename: str = 'plane_war_save.json'):
        """
        初始化存档管理器

        Args:
            filename: 存档文件名
        """
        self.store = JsonStore(filename)

    def save_game(self, game_state: Dict[str, Any]) -> None:
        """
        保存游戏状态

        Args:
            game_state: 游戏状态字典
        """
        self.store.put('game', **game_state)

    def load_game(self) -> Dict[str, Any]:
        """
        加载游戏状态

        Returns:
            游戏状态字典
        """
        if self.store.exists('game'):
            return dict(self.store.get('game'))
        return {}

    def has_save(self) -> bool:
        """检查是否有存档"""
        return self.store.exists('game')

    def delete_save(self) -> None:
        """删除存档"""
        if self.store.exists('game'):
            self.store.delete('game')

    def save_high_score(self, score: int) -> None:
        """
        保存最高分

        Args:
            score: 分数
        """
        current = self.get_high_score()
        if score > current:
            self.store.put('high_score', value=score)

    def get_high_score(self) -> int:
        """
        获取最高分

        Returns:
            最高分
        """
        if self.store.exists('high_score'):
            return self.store.get('high_score').get('value', 0)
        return 0

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """
        保存设置

        Args:
            settings: 设置字典
        """
        self.store.put('settings', **settings)

    def load_settings(self) -> Dict[str, Any]:
        """
        加载设置

        Returns:
            设置字典
        """
        if self.store.exists('settings'):
            return dict(self.store.get('settings'))
        return {
            'music_volume': 0.7,
            'sfx_volume': 0.8,
            'sound_enabled': True,
            'difficulty': 'normal',
        }

    def save_achievements(self, achievements: Dict[str, Any]) -> None:
        """
        保存成就

        Args:
            achievements: 成就字典
        """
        self.store.put('achievements', **achievements)

    def load_achievements(self) -> Dict[str, Any]:
        """
        加载成就

        Returns:
            成就字典
        """
        if self.store.exists('achievements'):
            return dict(self.store.get('achievements'))
        return {}

    def save_statistics(self, stats: Dict[str, Any]) -> None:
        """
        保存统计数据

        Args:
            stats: 统计字典
        """
        self.store.put('statistics', **stats)

    def load_statistics(self) -> Dict[str, Any]:
        """
        加载统计数据

        Returns:
            统计字典
        """
        if self.store.exists('statistics'):
            return dict(self.store.get('statistics'))
        return {
            'total_games': 0,
            'total_score': 0,
            'total_enemies_killed': 0,
            'total_bosses_killed': 0,
            'max_level_reached': 0,
        }

    def update_statistics(self, updates: Dict[str, Any]) -> None:
        """
        更新统计数据

        Args:
            updates: 更新字典
        """
        stats = self.load_statistics()
        for key, value in updates.items():
            if key in stats:
                if isinstance(value, int) and isinstance(stats[key], int):
                    stats[key] += value
                else:
                    stats[key] = value
            else:
                stats[key] = value
        self.save_statistics(stats)

    def clear_all(self) -> None:
        """清空所有存档"""
        for key in ['game', 'high_score', 'settings', 'achievements', 'statistics']:
            if self.store.exists(key):
                self.store.delete(key)


# 全局存档管理器
save_manager = SaveManager()


def get_save() -> SaveManager:
    """获取全局存档管理器"""
    return save_manager
