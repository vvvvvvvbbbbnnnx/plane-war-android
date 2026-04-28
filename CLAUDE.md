# plane-war-android

## 项目概述

Kivy 框架开发的 2D 竖版弹幕射击游戏（飞机大战），支持 Android 打包。模块化架构，配置/核心/实体/系统/UI 六层分离。

## 技术栈

- Python 3 + Kivy
- Buildozer 打包 Android APK
- GitHub Actions 自动构建发布

## 注意事项

- 所有资源通过 `utils/resources.py` 的 `ResourceManager` 统一管理
- 屏幕适配通过 `utils/screen.py` 处理
- 游戏核心循环在 `core/game.py` 的 `Game` 类中
- 配置项集中在 `config/settings.py` 的 `GameConfig` dataclass
