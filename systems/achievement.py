# -*- coding: utf-8 -*-
"""
飞机大战 - 成就系统

管理游戏成就的解锁和显示
"""
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from systems.save import save_manager


@dataclass
class Achievement:
    """
    成就数据类

    Attributes:
        id: 成就ID
        name: 成就名称
        description: 成就描述
        icon: 图标名称
        unlocked: 是否解锁
        progress: 当前进度
        target: 目标值
        hidden: 是否隐藏
    """
    id: str
    name: str
    description: str
    icon: str = 'star.png'
    unlocked: bool = False
    progress: int = 0
    target: int = 1
    hidden: bool = False


class AchievementManager:
    """
    成就管理器

    Attributes:
        achievements: 成就字典
        on_unlock: 成就解锁回调
    """

    def __init__(self):
        """初始化成就管理器"""
        # 定义所有成就
        self.achievements: Dict[str, Achievement] = {
            # 击杀成就
            'first_blood': Achievement(
                'first_blood', '初次击杀', '击败第一个敌人',
                'star.png', target=1
            ),
            'killer_10': Achievement(
                'killer_10', '小试牛刀', '累计击败10个敌人',
                'target.png', target=10
            ),
            'killer_100': Achievement(
                'killer_100', '杀敌如麻', '累计击败100个敌人',
                'target.png', target=100
            ),
            'killer_1000': Achievement(
                'killer_1000', '死神降临', '累计击败1000个敌人',
                'skull.png', target=1000
            ),

            # 分数成就
            'score_1000': Achievement(
                'score_1000', '得分达人', '单局得分超过1000',
                'trophy.png', target=1000
            ),
            'score_5000': Achievement(
                'score_5000', '高分玩家', '单局得分超过5000',
                'trophy.png', target=5000
            ),
            'score_10000': Achievement(
                'score_10000', '分数大师', '单局得分超过10000',
                'trophy.png', target=10000
            ),

            # 关卡成就
            'level_3': Achievement(
                'level_3', '初窥门径', '到达第3关',
                'medal.png', target=3
            ),
            'level_5': Achievement(
                'level_5', '渐入佳境', '到达第5关',
                'medal.png', target=5
            ),
            'level_10': Achievement(
                'level_10', '关卡大师', '到达第10关',
                'medal.png', target=10
            ),

            # Boss成就
            'boss_first': Achievement(
                'boss_first', 'Boss杀手', '击败第一个Boss',
                'boss.png', target=1
            ),
            'boss_5': Achievement(
                'boss_5', 'Boss克星', '累计击败5个Boss',
                'boss.png', target=5
            ),
            'boss_10': Achievement(
                'boss_10', 'Boss终结者', '累计击败10个Boss',
                'boss.png', target=10
            ),

            # 特殊成就
            'no_damage': Achievement(
                'no_damage', '无伤通关', '不受伤完成一关',
                'shield.png', hidden=True
            ),
            'bomb_master': Achievement(
                'bomb_master', '炸弹专家', '单局使用5次炸弹',
                'bomb.png', target=5
            ),
            'powerup_collector': Achievement(
                'powerup_collector', '道具收集者', '单局收集10个道具',
                'box.png', target=10
            ),
        }

        # 解锁回调
        self.on_unlock: Optional[Callable[[Achievement], None]] = None

        # 从存档加载
        self._load_from_save()

    def _load_from_save(self) -> None:
        """从存档加载成就状态"""
        saved = save_manager.load_achievements()
        for achievement_id, data in saved.items():
            if achievement_id in self.achievements:
                achievement = self.achievements[achievement_id]
                achievement.unlocked = data.get('unlocked', False)
                achievement.progress = data.get('progress', 0)

    def _save_to_save(self) -> None:
        """保存成就状态到存档"""
        data = {
            aid: {
                'unlocked': a.unlocked,
                'progress': a.progress
            }
            for aid, a in self.achievements.items()
        }
        save_manager.save_achievements(data)

    def check_achievement(self, achievement_id: str, value: int) -> bool:
        """
        检查成就进度

        Args:
            achievement_id: 成就ID
            value: 当前进度值

        Returns:
            是否新解锁
        """
        if achievement_id not in self.achievements:
            return False

        achievement = self.achievements[achievement_id]

        # 已解锁则跳过
        if achievement.unlocked:
            return False

        # 更新进度
        achievement.progress = value

        # 检查是否解锁
        if value >= achievement.target:
            achievement.unlocked = True
            self._save_to_save()

            # 触发回调
            if self.on_unlock:
                self.on_unlock(achievement)

            return True

        return False

    def increment_achievement(self, achievement_id: str, amount: int = 1) -> bool:
        """
        增加成就进度

        Args:
            achievement_id: 成就ID
            amount: 增加量

        Returns:
            是否新解锁
        """
        if achievement_id not in self.achievements:
            return False

        achievement = self.achievements[achievement_id]
        return self.check_achievement(achievement_id, achievement.progress + amount)

    def unlock_achievement(self, achievement_id: str) -> bool:
        """
        直接解锁成就

        Args:
            achievement_id: 成就ID

        Returns:
            是否成功解锁
        """
        if achievement_id not in self.achievements:
            return False

        achievement = self.achievements[achievement_id]

        if achievement.unlocked:
            return False

        achievement.unlocked = True
        achievement.progress = achievement.target
        self._save_to_save()

        if self.on_unlock:
            self.on_unlock(achievement)

        return True

    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """获取成就"""
        return self.achievements.get(achievement_id)

    def get_all_achievements(self) -> List[Achievement]:
        """获取所有成就"""
        return list(self.achievements.values())

    def get_unlocked_achievements(self) -> List[Achievement]:
        """获取已解锁的成就"""
        return [a for a in self.achievements.values() if a.unlocked]

    def get_visible_achievements(self) -> List[Achievement]:
        """获取可见的成就（非隐藏或已解锁）"""
        return [
            a for a in self.achievements.values()
            if not a.hidden or a.unlocked
        ]

    def get_progress(self, achievement_id: str) -> float:
        """
        获取成就进度比例

        Args:
            achievement_id: 成就ID

        Returns:
            进度比例 (0-1)
        """
        achievement = self.achievements.get(achievement_id)
        if not achievement:
            return 0.0
        return min(1.0, achievement.progress / achievement.target)

    def get_unlocked_count(self) -> int:
        """获取已解锁成就数量"""
        return sum(1 for a in self.achievements.values() if a.unlocked)

    def get_total_count(self) -> int:
        """获取成就总数"""
        return len(self.achievements)

    def reset_all(self) -> None:
        """重置所有成就（用于测试）"""
        for achievement in self.achievements.values():
            achievement.unlocked = False
            achievement.progress = 0
        self._save_to_save()


# 全局成就管理器
achievement_manager = AchievementManager()


def get_achievements() -> AchievementManager:
    """获取全局成就管理器"""
    return achievement_manager
