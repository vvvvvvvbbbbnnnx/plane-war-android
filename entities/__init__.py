# -*- coding: utf-8 -*-
"""飞机大战 - 实体模块"""
# 避免循环导入，使用延迟导入
# from .player import Player
# from .enemy import Enemy
# from .boss import Boss
# from .bullet import Bullet
# from .powerup import PowerUp
# from .explosion import Explosion

__all__ = ['Player', 'Enemy', 'Boss', 'Bullet', 'PowerUp', 'Explosion']


def __getattr__(name):
    """延迟导入"""
    if name == 'Player':
        from .player import Player
        return Player
    elif name == 'Enemy':
        from .enemy import Enemy
        return Enemy
    elif name == 'Boss':
        from .boss import Boss
        return Boss
    elif name == 'Bullet':
        from .bullet import Bullet
        return Bullet
    elif name == 'PowerUp':
        from .powerup import PowerUp
        return PowerUp
    elif name == 'Explosion':
        from .explosion import Explosion
        return Explosion
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
