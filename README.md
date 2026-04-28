# 飞机大战 - Android版

一个使用 Kivy 框架开发的 2D 竖版弹幕射击游戏，支持 Android 打包。

## 游戏特性

- 3 种敌机类型（普通/快速/重型）+ Boss 战
- 4 种道具（血量/武器/护盾/炸弹）
- 10 个递增关卡
- 爆炸帧动画、粒子效果
- 成就系统、存档系统
- 自适应屏幕尺寸

## 快速开始

```bash
pip install kivy
python main.py
```

## 游戏操作

- **移动飞机**: 触摸/鼠标拖动
- **射击**: 自动射击
- **炸弹**: 双击屏幕
- **暂停**: ESC 键

## 打包 Android APK

### GitHub Actions（自动打包）

推送代码到 main 分支自动触发构建，在 [Releases](https://github.com/vvvvvvvbbbbnnnx/plane-war-android/releases) 下载 APK。

### 本地打包

```bash
# WSL 中安装依赖
sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool \
  pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 \
  cmake libffi-dev libssl-dev automake
pip3 install --user buildozer cython

# 打包
buildozer android debug
```

## 项目结构

```
├── main.py              # 入口文件
├── buildozer.spec       # Android 打包配置
├── config/              # 游戏配置
├── core/                # 核心引擎（实体基类、游戏循环、对象池）
├── entities/            # 游戏实体（玩家、敌机、Boss、子弹、道具、爆炸）
├── systems/             # 游戏系统（碰撞、音效、粒子、成就、存档）
├── ui/                  # UI 组件（菜单、HUD、暂停、游戏结束、设置）
├── utils/               # 工具模块（屏幕适配、资源管理）
└── assets/              # 资源文件
    ├── images/          # 精灵图片
    ├── sounds/          # 音效
    ├── fonts/           # 字体
    └── explosion/       # 爆炸动画帧
```

## 素材来源

游戏素材来自 [Kenney.nl](https://kenney.nl) 的 Tappy Plane 素材包，CC0 许可。
