# -*- coding: utf-8 -*-
"""
飞机大战图形资源生成器
生成精美的游戏图形资源
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math

# 输出目录
OUTPUT_DIR = r"C:\Users\Admin\Desktop\新建文件夹"

# 颜色定义
COLORS = {
    'cyan': (50, 255, 255),
    'blue': (50, 150, 255),
    'dark_blue': (30, 100, 200),
    'red': (255, 50, 50),
    'dark_red': (180, 30, 30),
    'orange': (255, 150, 50),
    'yellow': (255, 255, 50),
    'green': (50, 255, 100),
    'purple': (200, 100, 255),
    'white': (255, 255, 255),
    'gray': (100, 100, 100),
    'dark_gray': (60, 60, 60),
    'gold': (255, 215, 0),
}


def create_gradient(draw, x1, y1, x2, y2, color1, color2, direction='vertical'):
    """创建渐变效果"""
    if direction == 'vertical':
        for y in range(y1, y2):
            ratio = (y - y1) / (y2 - y1) if y2 != y1 else 0
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            draw.line([(x1, y), (x2, y)], fill=(r, g, b))
    else:
        for x in range(x1, x2):
            ratio = (x - x1) / (x2 - x1) if x2 != x1 else 0
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            draw.line([(x, y1), (x, y2)], fill=(r, g, b))


def add_glow(image, color, radius=3):
    """添加发光效果"""
    glow = Image.new('RGBA', image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    # 复制原图轮廓
    for x in range(image.width):
        for y in range(image.height):
            pixel = image.getpixel((x, y))
            if pixel[3] > 0:
                glow_draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                                  fill=(*color, 50))

    glow = glow.filter(ImageFilter.GaussianBlur(radius))
    result = Image.alpha_composite(glow, image)
    return result


def create_player_ship():
    """创建精美的玩家飞机"""
    size = (80, 100)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 主体 - 流线型机身
    body_points = [
        (40, 5),   # 顶部尖端
        (30, 30),  # 上部
        (25, 50),  # 中部
        (20, 75),  # 下部
        (40, 85),  # 尾部中心
        (60, 75),  # 下部
        (55, 50),  # 中部
        (50, 30),  # 上部
    ]
    draw.polygon(body_points, fill=COLORS['cyan'])

    # 机身渐变效果（高光）
    highlight_points = [
        (40, 10),
        (35, 35),
        (32, 55),
        (40, 70),
        (48, 55),
        (45, 35),
    ]
    draw.polygon(highlight_points, fill=(100, 255, 255))

    # 左机翼
    wing_left = [
        (25, 50),
        (5, 80),
        (10, 85),
        (25, 75),
    ]
    draw.polygon(wing_left, fill=COLORS['blue'])

    # 右机翼
    wing_right = [
        (55, 50),
        (75, 80),
        (70, 85),
        (55, 75),
    ]
    draw.polygon(wing_right, fill=COLORS['blue'])

    # 驾驶舱
    draw.ellipse([32, 25, 48, 50], fill=COLORS['white'])
    draw.ellipse([35, 28, 45, 45], fill=(150, 220, 255))

    # 引擎
    draw.rectangle([35, 75, 45, 95], fill=COLORS['dark_gray'])
    draw.ellipse([36, 90, 44, 98], fill=COLORS['orange'])  # 火焰

    # 添加发光效果
    img = add_glow(img, COLORS['cyan'], 2)

    return img


def create_enemy_normal():
    """创建普通敌机"""
    size = (50, 50)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 主体
    body = [
        (25, 45),  # 底部
        (5, 10),   # 左上
        (25, 20),  # 中间凹陷
        (45, 10),  # 右上
    ]
    draw.polygon(body, fill=COLORS['red'])

    # 高光
    highlight = [
        (25, 40),
        (15, 15),
        (25, 22),
        (35, 15),
    ]
    draw.polygon(highlight, fill=COLORS['orange'])

    # 驾驶舱
    draw.ellipse([20, 12, 30, 25], fill=COLORS['dark_red'])

    # 引擎
    draw.ellipse([20, 5, 25, 10], fill=COLORS['orange'])
    draw.ellipse([25, 5, 30, 10], fill=COLORS['orange'])

    return img


def create_enemy_fast():
    """创建快速敌机"""
    size = (40, 45)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 流线型主体
    body = [
        (20, 42),
        (3, 5),
        (20, 15),
        (37, 5),
    ]
    draw.polygon(body, fill=COLORS['purple'])

    # 高光
    highlight = [
        (20, 38),
        (10, 10),
        (20, 18),
        (30, 10),
    ]
    draw.polygon(highlight, fill=(220, 150, 255))

    # 引擎
    draw.ellipse([15, 2, 25, 8], fill=COLORS['orange'])

    return img


def create_enemy_tank():
    """创建坦克敌机"""
    size = (70, 60)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 主体 - 厚重装甲
    draw.rounded_rectangle([10, 15, 60, 55], radius=8, fill=COLORS['dark_gray'])
    draw.rounded_rectangle([15, 20, 55, 50], radius=5, fill=COLORS['red'])

    # 装甲板
    draw.rectangle([20, 25, 50, 45], fill=COLORS['dark_red'])

    # 炮塔
    draw.rectangle([30, 5, 40, 20], fill=COLORS['gray'])
    draw.ellipse([28, 0, 42, 15], fill=COLORS['dark_gray'])

    # 引擎
    draw.ellipse([25, 50, 35, 58], fill=COLORS['orange'])
    draw.ellipse([35, 50, 45, 58], fill=COLORS['orange'])

    return img


def create_boss(level=1):
    """创建Boss"""
    size = 150 + level * 15
    width = size
    height = size // 2
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 主体 - 椭圆形
    draw.ellipse([0, 0, width, height], fill=COLORS['dark_red'])
    draw.ellipse([10, 5, width-10, height-5], fill=COLORS['red'])

    # 装甲带
    draw.rectangle([0, height//3, width, height*2//3], fill=(100, 0, 0))

    # 核心
    cx, cy = width // 2, height // 2
    draw.ellipse([cx-25, cy-25, cx+25, cy+25], fill=COLORS['gold'])
    draw.ellipse([cx-15, cy-15, cx+15, cy+15], fill=COLORS['white'])

    # 武器口
    for i in range(3):
        x = width // 4 + i * width // 4
        draw.ellipse([x-8, height-15, x+8, height], fill=COLORS['dark_gray'])

    # 添加发光
    img = add_glow(img, COLORS['red'], 3)

    return img


def create_player_bullet():
    """创建玩家子弹"""
    size = (12, 30)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 子弹主体
    draw.ellipse([0, 0, 12, 30], fill=COLORS['cyan'])
    draw.ellipse([2, 3, 10, 27], fill=COLORS['white'])

    # 发光效果
    img = add_glow(img, COLORS['cyan'], 2)

    return img


def create_enemy_bullet():
    """创建敌方子弹"""
    size = (14, 20)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse([0, 0, 14, 20], fill=COLORS['red'])
    draw.ellipse([3, 3, 11, 17], fill=COLORS['orange'])

    return img


def create_powerup_health():
    """创建生命道具"""
    size = (40, 40)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 圆形背景
    draw.ellipse([2, 2, 38, 38], fill=COLORS['green'])
    draw.ellipse([5, 5, 35, 35], fill=(80, 255, 130))

    # 十字
    draw.rectangle([16, 10, 24, 30], fill=COLORS['white'])
    draw.rectangle([10, 16, 30, 24], fill=COLORS['white'])

    return img


def create_powerup_weapon():
    """创建武器道具"""
    size = (40, 40)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 闪电形状
    bolt = [
        (22, 2),
        (10, 18),
        (18, 18),
        (16, 38),
        (30, 20),
        (22, 20),
    ]
    draw.polygon(bolt, fill=COLORS['yellow'])
    draw.polygon([(20, 8), (14, 18), (20, 18), (18, 30), (26, 20), (20, 20)], fill=COLORS['gold'])

    return img


def create_powerup_shield():
    """创建护盾道具"""
    size = (40, 40)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 护盾形状
    draw.ellipse([5, 5, 35, 35], outline=COLORS['cyan'], width=4)
    draw.ellipse([10, 10, 30, 30], outline=COLORS['white'], width=2)

    return img


def create_powerup_bomb():
    """创建炸弹道具"""
    size = (40, 40)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 炸弹主体
    draw.ellipse([8, 12, 32, 36], fill=COLORS['dark_gray'])
    draw.ellipse([10, 14, 30, 34], fill=COLORS['gray'])

    # 引信
    draw.rectangle([18, 5, 22, 15], fill=COLORS['orange'])
    draw.ellipse([15, 2, 25, 8], fill=COLORS['yellow'])

    return img


def create_explosion_frames(size=60, frames=15):
    """创建爆炸动画帧"""
    frames_list = []
    for i in range(frames):
        img = Image.new('RGBA', (size*2, size*2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        progress = i / frames
        radius = int(size * progress)
        alpha = int(255 * (1 - progress))

        colors = [
            (255, 255, 200, alpha),
            (255, 200, 50, alpha),
            (255, 100, 0, alpha),
        ]

        for j, color in enumerate(colors):
            r = max(1, radius - j * 8)
            draw.ellipse([size-r, size-r, size+r, size+r], fill=color)

        frames_list.append(img)

    return frames_list


def create_background():
    """创建星空背景"""
    size = (480, 700)
    img = Image.new('RGB', size, (10, 15, 40))
    draw = ImageDraw.Draw(img)

    # 添加渐变
    for y in range(size[1]):
        ratio = y / size[1]
        r = int(10 + 15 * ratio)
        g = int(15 + 20 * ratio)
        b = int(40 + 30 * ratio)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))

    # 添加星星
    import random
    random.seed(42)
    for _ in range(150):
        x = random.randint(0, size[0]-1)
        y = random.randint(0, size[1]-1)
        brightness = random.randint(100, 255)
        star_size = random.randint(1, 3)
        draw.ellipse([x, y, x+star_size, y+star_size], fill=(brightness, brightness, brightness))

    return img


def main():
    """生成所有资源"""
    print("正在生成图形资源...")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    resources = {
        'player.png': create_player_ship(),
        'enemy_normal.png': create_enemy_normal(),
        'enemy_fast.png': create_enemy_fast(),
        'enemy_tank.png': create_enemy_tank(),
        'boss.png': create_boss(),
        'bullet_player.png': create_player_bullet(),
        'bullet_enemy.png': create_enemy_bullet(),
        'powerup_health.png': create_powerup_health(),
        'powerup_weapon.png': create_powerup_weapon(),
        'powerup_shield.png': create_powerup_shield(),
        'powerup_bomb.png': create_powerup_bomb(),
        'background.png': create_background(),
    }

    # 保存资源
    for filename, img in resources.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath)
        print(f"  已生成: {filename}")

    # 生成爆炸动画帧
    print("  正在生成爆炸动画...")
    explosion_frames = create_explosion_frames()
    for i, frame in enumerate(explosion_frames):
        filepath = os.path.join(OUTPUT_DIR, f'explosion_{i:02d}.png')
        frame.save(filepath)
    print(f"  已生成: explosion_00.png - explosion_{len(explosion_frames)-1:02d}.png")

    print(f"\n所有资源已保存到: {OUTPUT_DIR}")
    print("共生成", len(resources) + len(explosion_frames), "个文件")


if __name__ == '__main__':
    main()
