# plane-war-refactor

## 项目概述

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/) [![Kivy](https://img.shields.io/badge/kivy-2.2+-green.svg)](https://kivy.org/) [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) [![CI/CD](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/vvvvvvvvbbbbnnnx/plane-war-android/actions)

## 目录结构

```
plane-war-refactor/
├── assets/
│   ├── explosion/
│   │   ├── Explosion1.png
│   │   ├── Explosion2.png
│   │   ├── Explosion3.png
│   │   ├── Explosion4.png
│   │   ├── Explosion5.png
│   │   └── ... (2 more files)
│   ├── fonts/
│   ├── images/
│   │   ├── background.png
│   │   ├── boss.png
│   │   ├── bullet_enemy.png
│   │   ├── bullet_player.png
│   │   ├── enemy_fast.png
│   │   └── ... (22 more files)
│   ├── plane_sprite/
│   └── sounds/
│       ├── bgm.wav
│       ├── bomb.wav
│       ├── boss.wav
│       ├── boss_death.wav
│       ├── button.wav
│       └── ... (4 more files)
├── config/
│   ├── __init__.py
│   ├── settings.py
├── core/
│   ├── __init__.py
│   ├── entity.py
│   ├── game.py
│   ├── pool.py
│   └── scene.py
├── entities/
│   ├── __init__.py
│   ├── boss.py
│   ├── bullet.py
│   ├── enemy.py
│   ├── explosion.py
│   └── ... (2 more files)
├── systems/
│   ├── __init__.py
│   ├── achievement.py
│   ├── audio.py
│   ├── collision.py
│   ├── particle.py
│   └── ... (1 more files)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_achievement.py
│   ├── test_collision.py
│   ├── test_config.py
│   └── ... (2 more files)
├── ui/
│   ├── __init__.py
│   ├── game_over.py
│   ├── hud.py
│   ├── menu.py
│   ├── pause.py
│   └── ... (1 more files)
├── utils/
│   ├── __init__.py
│   ├── helpers.py
│   ├── resources.py
│   ├── screen.py
├── README_ANDROID.md
├── buildozer.spec
├── main.py
├── pixel_shmup.zip
├── plane_war_save.json
└── ... (4 more files)
```

## 技术栈

- **编程语言**: Python
- **工具**: GitHub Actions
- **包管理**: poetry/pip

## 开发命令

- **测试**: `pytest`

## 备注

- 此文件由 Claude Code 自动生成
- 最后更新: 2026-05-03 01:16:51
