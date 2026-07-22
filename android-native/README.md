# 飞机大战 (Plane War)

一个纯 Kotlin + SurfaceView 自绘的经典竖版飞机大战 Android 游戏，无需任何图片素材，所有图形均由 Canvas 代码绘制。

## 玩法

- 点击屏幕开始游戏
- 按住并拖动手指移动战机（战机显示在手指上方，避免遮挡）
- 战机自动开火，得分超过 **300** 后解锁双发子弹
- 敌机分三种：
  - 小型机（红）：1 血，速度快，10 分
  - 中型机（紫）：3 血，会漂移，30 分
  - 大型机（橙）：6 血，会朝玩家反击，60 分
- 被敌机撞击或中弹损失 1 条命（受击后 1.5 秒无敌闪烁），共 3 条命
- 游戏结束后点击屏幕重新开始，最高分手动保存在本地

## 特性

- SurfaceView 独立线程游戏循环，按 dt（秒）驱动，帧率无关
- 三层视差滚动星空背景
- 爆炸粒子特效、引擎尾焰动画
- 敌机血条、HUD 计分 / 生命值显示
- 难度随分数递增（刷怪更快、大敌机更多）

## 技术栈

- Kotlin
- AndroidX AppCompat
- minSdk 24 / targetSdk 34
- 无第三方游戏引擎，零图片资源

## 构建

用 **Android Studio** (Hedgehog+) 打开本目录，等待 Gradle Sync 完成后直接 Run 即可；
或命令行（需要本机已安装 Gradle 与 Android SDK）：

```bash
gradle assembleDebug
```

APK 输出于 `app/build/outputs/apk/debug/app-debug.apk`。

## 项目结构

```
app/src/main/java/com/vbnx/planewar/
├── MainActivity.kt        # 全屏竖屏入口
├── GameView.kt            # 游戏循环、输入、刷怪、碰撞、渲染、HUD
└── game/
    ├── Player.kt          # 玩家战机
    ├── Enemy.kt           # 敌机（3 种类型 + 反击 AI）
    ├── Bullet.kt          # 子弹（敌我）
    ├── Explosion.kt       # 爆炸粒子
    └── StarField.kt       # 星空背景
```
