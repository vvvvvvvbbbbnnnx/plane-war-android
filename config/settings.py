# -*- coding: utf-8 -*-
"""
游戏配置模块
所有游戏常量和配置集中管理
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import json
import os


@dataclass
class PlayerConfig:
    """玩家配置"""
    max_health: int = 3
    max_weapon_level: int = 3
    base_speed: float = 8.0
    invincible_time: float = 2.0
    shield_duration: float = 5.0
    max_bombs: int = 5
    max_lives: int = 5


@dataclass
class EnemyConfig:
    """敌机配置"""
    health: int = 1
    speed: float = 3.0
    score: int = 100
    shoot_probability: float = 0.005
    width_ratio: float = 0.08
    height_ratio: float = 0.05


@dataclass
class BossConfig:
    """Boss配置"""
    base_health: int = 20
    health_per_level: int = 10
    base_score: int = 1000
    speed: float = 1.5
    shoot_interval: float = 0.5
    width_ratio: float = 0.25
    height_ratio: float = 0.1


@dataclass
class BulletConfig:
    """子弹配置"""
    player_speed: float = 12.0
    enemy_speed: float = 4.0
    player_width_ratio: float = 0.02
    player_height_ratio: float = 0.03
    enemy_width_ratio: float = 0.025
    enemy_height_ratio: float = 0.025


@dataclass
class PowerUpConfig:
    """道具配置"""
    drop_rate: float = 0.15
    speed: float = 2.0
    width_ratio: float = 0.07
    height_ratio: float = 0.04
    types: List[str] = field(default_factory=lambda: ['health', 'weapon', 'shield', 'bomb'])


@dataclass
class LevelConfig:
    """关卡配置"""
    level: int = 1
    enemies_to_kill: int = 15
    spawn_rate: float = 1.5
    enemy_types: List[str] = field(default_factory=lambda: ['normal'])
    boss_health: int = 20


@dataclass
class GameConfig:
    """游戏主配置"""
    # 设计基准尺寸
    design_width: int = 720
    design_height: int = 1280

    # 游戏参数
    shoot_cooldown: float = 0.15
    double_tap_threshold: float = 0.3
    target_fps: int = 60

    # 实体配置
    player: PlayerConfig = field(default_factory=PlayerConfig)
    enemies: Dict[str, EnemyConfig] = field(default_factory=dict)
    boss: BossConfig = field(default_factory=BossConfig)
    bullet: BulletConfig = field(default_factory=BulletConfig)
    powerup: PowerUpConfig = field(default_factory=PowerUpConfig)

    # 关卡配置
    levels: List[LevelConfig] = field(default_factory=list)

    # 音效配置
    sound_enabled: bool = True
    music_volume: float = 0.7
    sfx_volume: float = 0.8

    def __post_init__(self):
        """初始化默认配置"""
        if not self.enemies:
            self.enemies = {
                'normal': EnemyConfig(
                    health=1, speed=3.0, score=100,
                    width_ratio=0.08, height_ratio=0.05
                ),
                'fast': EnemyConfig(
                    health=1, speed=5.0, score=150,
                    width_ratio=0.06, height_ratio=0.04,
                    shoot_probability=0.008
                ),
                'tank': EnemyConfig(
                    health=3, speed=2.0, score=300,
                    width_ratio=0.11, height_ratio=0.06,
                    shoot_probability=0.01
                ),
            }

        if not self.levels:
            self.levels = self._generate_levels()

    def _generate_levels(self) -> List[LevelConfig]:
        """生成关卡配置"""
        levels = []
        for i in range(1, 11):
            if i < 3:
                enemy_types = ['normal']
            elif i < 6:
                enemy_types = ['normal', 'fast']
            else:
                enemy_types = ['normal', 'fast', 'tank']

            levels.append(LevelConfig(
                level=i,
                enemies_to_kill=10 + i * 5,
                spawn_rate=max(0.5, 2 - i * 0.1),
                enemy_types=enemy_types,
                boss_health=self.boss.base_health + i * self.boss.health_per_level
            ))
        return levels

    def get_level(self, level: int) -> LevelConfig:
        """获取指定关卡配置"""
        if level < 1:
            level = 1
        if level > len(self.levels):
            level = len(self.levels)
        return self.levels[level - 1]

    @classmethod
    def load(cls, path: str) -> 'GameConfig':
        """从JSON文件加载配置"""
        if not os.path.exists(path):
            return cls()

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 解析嵌套配置
        config = cls()

        if 'player' in data:
            config.player = PlayerConfig(**data['player'])

        if 'enemies' in data:
            config.enemies = {
                k: EnemyConfig(**v) for k, v in data['enemies'].items()
            }

        if 'boss' in data:
            config.boss = BossConfig(**data['boss'])

        if 'bullet' in data:
            config.bullet = BulletConfig(**data['bullet'])

        if 'powerup' in data:
            config.powerup = PowerUpConfig(**data['powerup'])

        # 更新其他字段
        for key in ['design_width', 'design_height', 'shoot_cooldown',
                    'double_tap_threshold', 'target_fps', 'sound_enabled',
                    'music_volume', 'sfx_volume']:
            if key in data:
                setattr(config, key, data[key])

        return config

    def save(self, path: str) -> None:
        """保存配置到JSON文件"""
        data = {
            'design_width': self.design_width,
            'design_height': self.design_height,
            'shoot_cooldown': self.shoot_cooldown,
            'double_tap_threshold': self.double_tap_threshold,
            'target_fps': self.target_fps,
            'sound_enabled': self.sound_enabled,
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume,
            'player': {
                'max_health': self.player.max_health,
                'max_weapon_level': self.player.max_weapon_level,
                'base_speed': self.player.base_speed,
                'invincible_time': self.player.invincible_time,
                'shield_duration': self.player.shield_duration,
                'max_bombs': self.player.max_bombs,
                'max_lives': self.player.max_lives,
            },
            'enemies': {
                k: {
                    'health': v.health,
                    'speed': v.speed,
                    'score': v.score,
                    'shoot_probability': v.shoot_probability,
                    'width_ratio': v.width_ratio,
                    'height_ratio': v.height_ratio,
                }
                for k, v in self.enemies.items()
            },
            'boss': {
                'base_health': self.boss.base_health,
                'health_per_level': self.boss.health_per_level,
                'base_score': self.boss.base_score,
                'speed': self.boss.speed,
                'shoot_interval': self.boss.shoot_interval,
                'width_ratio': self.boss.width_ratio,
                'height_ratio': self.boss.height_ratio,
            },
            'bullet': {
                'player_speed': self.bullet.player_speed,
                'enemy_speed': self.bullet.enemy_speed,
                'player_width_ratio': self.bullet.player_width_ratio,
                'player_height_ratio': self.bullet.player_height_ratio,
                'enemy_width_ratio': self.bullet.enemy_width_ratio,
                'enemy_height_ratio': self.bullet.enemy_height_ratio,
            },
            'powerup': {
                'drop_rate': self.powerup.drop_rate,
                'speed': self.powerup.speed,
                'width_ratio': self.powerup.width_ratio,
                'height_ratio': self.powerup.height_ratio,
                'types': self.powerup.types,
            },
        }

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# 全局配置实例
_config: Optional[GameConfig] = None


def get_config() -> GameConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = GameConfig()
    return _config


def set_config(config: GameConfig) -> None:
    """设置全局配置"""
    global _config
    _config = config
