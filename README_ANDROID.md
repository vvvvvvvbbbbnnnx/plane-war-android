# 飞机大战 Android版

## 文件说明

- `plane_war_android.py` - 游戏主程序（Kivy框架）
- `buildozer.spec` - 打包配置文件

## 在Windows上测试运行

首先安装Kivy：
```bash
pip install kivy
```

然后运行游戏：
```bash
python plane_war_android.py
```

## 打包成APK

### 方法一：使用Buildozer（推荐，需要Linux环境）

1. 在WSL2或Linux虚拟机中：
```bash
# 安装依赖
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 安装Buildozer
pip install buildozer

# 进入项目目录
cd /mnt/c/Users/Admin/Desktop/新建文件夹

# 初始化（如果需要）
buildozer init

# 打包APK
buildozer -v android debug
```

打包完成后，APK文件在 `bin/` 目录下。

### 方法二：使用GitHub Actions自动打包

1. 将代码推送到GitHub仓库
2. 创建 `.github/workflows/build.yml`：

```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build with Buildozer
      uses: ArtemSBulgakov/buildozer-action@v1
      id: buildozer
      with:
        workdir: .
        buildozer_version: stable

    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: plane_war
        path: ${{ steps.buildozer.outputs.filename }}
```

3. 推送后，在Actions页面下载APK

### 方法三：使用在线打包服务

1. **Google Colab** - 上传代码后运行Buildozer
2. **Kivy Launcher** - 直接在手机上运行（需要安装Kivy Launcher应用）

## 游戏操作

- **移动飞机**：触摸屏幕并拖动
- **射击**：自动射击
- **炸弹**：双击屏幕使用炸弹（清屏）

## 游戏特性

- 10个关卡，难度递增
- 3种敌机类型（普通、快速、坦克）
- 每关Boss战
- 4种道具（生命、武器升级、护盾、炸弹）
- 触摸控制，适合移动设备
