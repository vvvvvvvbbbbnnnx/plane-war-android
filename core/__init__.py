"""飞机大战 - 核心模块"""
from .entity import Entity
from .pool import ObjectPool
from .scene import Scene, SceneManager

# Game 需要单独导入，避免循环导入
# from .game import Game

__all__ = ['Entity', 'ObjectPool', 'SceneManager', 'Scene']
