# 飞机大战 (Plane War) — Android 版

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Kivy](https://img.shields.io/badge/kivy-2.2+-green.svg)](https://kivy.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI/CD](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/vvvvvvvvbbbbnnnx/plane-war-android/actions)

一款基于 **Python/Kivy** 框架开发的商业级 2D 飞行射击手游，支持 Android 平台一键打包。

## 游戏截图

> *(运行 `python main.py` 体验)*

| 主菜单 | 游戏中 | Boss 战 |
|--------|--------|---------|
| 标题/高分/设置 | HUD/道具/敌机 | 血条/弹幕/击杀 |

## 核心特性

### 游戏玩法
- **10 个关卡**：难度递增，每关击杀达标后触发 Boss 战
- **3 种敌机类型**：普通（均衡）、快速（高速低血）、坦克（高血低速）
- **Boss 系统**：动态血条 / 三发射点齐射 / 体型随等级增长
- **4 种道具**：生命恢复 / 武器升级 / 护盾 / 炸弹
- **双击炸弹清屏**：对敌机秒杀，对 Boss 造成大量伤害

### 系统架构
- **ECS 模式**：Entity → Player/Enemy/Boss/Bullet/PowerUp/Explosion 实体分层
- **对象池 (Object Pool)**：子弹/敌机/道具复用，消除 GC 抖动
- **空间哈希碰撞检测**：O(n) 碰撞检测，分组注册回调制
- **成就系统**：15 种成就（击杀/分数/关卡/Boss/特殊条件），实时追踪 + 本地持久化
- **存档系统**：高分 / 设置 / 成就 / 统计数据 JSON 持久化
- **自适应分辨率**：720×1280 基准，9:16 竖屏，支持异形屏安全区
- **粒子特效**：爆炸/弹道拖尾/火花三种粒子效果

### 工程质量
- **完整类型标注**：核心模块 100% type hints（`Generic[T]`、`TypeVar`、`dataclass`）
- **配置驱动**：`GameConfig` dataclass，支持 JSON 导入导出，关卡数据代码生成
- **CI/CD 流水线**：ruff lint → mypy type check → pytest → APK 自动构建
- **测试覆盖**：config / pool / collision / save / achievement 纯逻辑模块全覆盖

## 技术栈

| 层级 | 技术 |
|------|------|
| 游戏引擎 | Kivy 2.2+ |
| 语言 | Python 3.9+ |
| 打包 | Buildozer |
| CI/CD | GitHub Actions |
| 代码质量 | ruff + mypy |
| 测试 | pytest + pytest-cov |

## 架构

```
plane-war-refactor/
├── config/          # 游戏配置（dataclass, JSON 序列化, 关卡生成）
├── core/            # 核心引擎
│   ├── entity.py    #   实体基类 (Entity → SpriteEntity)
│   ├── game.py      #   游戏主循环 (单例, 60FPS, 状态机)
│   ├── pool.py      #   泛型对象池 (MultiTypePool)
│   └── scene.py     #   场景基类
├── entities/        # 游戏实体
│   ├── player.py    #   玩家（血量/武器/护盾/炸弹/生命）
│   ├── enemy.py     #   敌机（3 种类型）
│   ├── boss.py      #   Boss（血条/多发射击）
│   ├── bullet.py    #   子弹（玩家/敌方双向）
│   ├── powerup.py   #   道具（4 种类型）
│   └── explosion.py #   爆炸（帧动画 / 粒子回退）
├── systems/         # 游戏系统
│   ├── collision.py #   空间哈希碰撞检测
│   ├── achievement.py # 成就管理器
│   ├── save.py      #   存档管理器
│   ├── audio.py     #   音效管理
│   └── particle.py  #   粒子系统
├── ui/              # 界面
│   ├── menu.py      #   主菜单
│   ├── hud.py       #   游戏内 HUD
│   ├── pause.py     #   暂停菜单
│   ├── game_over.py #   结算界面
│   └── settings.py  #   设置界面
├── utils/           # 工具
│   ├── screen.py    #   屏幕适配器
│   ├── resources.py #   资源管理器
│   └── helpers.py   #   数学/字体工具
├── tests/           # 测试套件
├── main.py          # 入口文件
├── buildozer.spec   # Android 打包配置
└── pyproject.toml   # 项目配置
```

## 快速开始

### 桌面运行

```bash
# 安装依赖
pip install kivy>=2.2.0

# 运行游戏
python main.py
```

### Android 打包

```bash
# 安装 Buildozer（需要 Linux 或 WSL）
pip install buildozer

# 打包 APK
buildozer android debug
```

或直接使用 GitHub Actions 自动构建（push 到 main 分支自动触发）。

### 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 代码检查
ruff check .
ruff format --check .

# 类型检查
mypy --ignore-missing-imports config/ core/ systems/ utils/

# 运行测试
pytest tests/ -v --tb=short

# 测试覆盖率
pytest tests/ -v --cov --cov-report=term-missing
```

## 游戏操作

| 操作 | 方式 |
|------|------|
| 移动飞机 | 触摸屏幕并拖动 |
| 射击 | 自动射击 |
| 炸弹 | 双击屏幕（清屏） |
| 暂停 | ESC 键 / 返回键 |

## License

MIT © 2026 vvvvvvvbbbbnnnx
