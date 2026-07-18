"""
飞机大战 - 工具函数

提供常用的工具函数。
"""
import math
import os
import random
from typing import Optional

from kivy.utils import platform

# 字体查找结果缓存：get_chinese_font 会被每个 Label 创建时调用，
# 每次遍历数十个 os.path.exists 是无谓开销，首次确定后 memoize。
_chinese_font_cache: Optional[str] = None
_chinese_font_resolved: bool = False


def get_chinese_font() -> Optional[str]:
    """
    获取支持中文的字体路径（结果缓存）

    Returns:
        字体路径，找不到返回None
    """
    global _chinese_font_cache, _chinese_font_resolved
    if _chinese_font_resolved:
        return _chinese_font_cache

    # 1) 优先使用项目自带字体（打包进 APK，跨平台一致，最可靠）
    try:
        from utils.resources import ResourceManager
        for fname in ('NotoSansSC-Regular.otf', 'noto.ttf', 'font.ttf'):
            p = ResourceManager.get_font_path(fname)
            if p and os.path.exists(p):
                _chinese_font_cache = p
                _chinese_font_resolved = True
                return p
    except Exception:
        pass

    # 2) 系统字体兜底
    # Android 系统字体路径
    android_fonts = [
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/NotoSansSC-Regular.otf',
        '/system/fonts/Roboto-Regular.ttf',
    ]

    # Windows 字体路径（.ttf 优先，Kivy 对 .ttc 支持不稳定）
    windows_fonts = [
        'C:/Windows/Fonts/simhei.ttf',   # 黑体（TrueType，最可靠）
        'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑（TrueType Collection）
        'C:/Windows/Fonts/simsun.ttc',    # 宋体
        'C:/Windows/Fonts/STZHONGS.TTF',  # 华文中宋
        'C:/Windows/Fonts/msyh.ttf',      # 微软雅黑（非 Collection 版本）
    ]

    # macOS 字体路径
    macos_fonts = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
    ]

    # Linux 字体路径
    linux_fonts = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    ]

    # 根据平台选择字体列表
    if platform == 'android':
        fonts = android_fonts
    elif platform == 'win':
        fonts = windows_fonts
    elif platform == 'macosx':
        fonts = macos_fonts
    elif platform == 'linux':
        fonts = linux_fonts
    else:
        fonts = android_fonts + windows_fonts + macos_fonts + linux_fonts

    # 查找存在的系统字体
    for font_path in fonts:
        if os.path.exists(font_path):
            _chinese_font_cache = os.path.normpath(font_path)
            _chinese_font_resolved = True
            return _chinese_font_cache

    # 全部找不到：缓存 None，避免每次调用都反复查找
    _chinese_font_cache = None
    _chinese_font_resolved = True
    return None


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    将值限制在指定范围内

    Args:
        value: 输入值
        min_val: 最小值
        max_val: 最大值

    Returns:
        限制后的值
    """
    return max(min_val, min(max_val, value))


def lerp(start: float, end: float, t: float) -> float:
    """
    线性插值

    Args:
        start: 起始值
        end: 结束值
        t: 插值因子 (0-1)

    Returns:
        插值结果
    """
    return start + (end - start) * t


def ease_in_quad(t: float) -> float:
    """二次缓入"""
    return t * t


def ease_out_quad(t: float) -> float:
    """二次缓出"""
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    """二次缓入缓出"""
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def ease_out_elastic(t: float) -> float:
    """弹性缓出"""
    if t == 0 or t == 1:
        return t

    p = 0.3
    s = p / 4
    return pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1


def ease_out_bounce(t: float) -> float:
    """弹跳缓出"""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    计算两点之间的距离

    Args:
        x1, y1: 第一个点
        x2, y2: 第二个点

    Returns:
        距离
    """
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def angle_between(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    计算两点之间的角度

    Args:
        x1, y1: 第一个点
        x2, y2: 第二个点

    Returns:
        角度（弧度）
    """
    return math.atan2(y2 - y1, x2 - x1)


def normalize_angle(angle: float) -> float:
    """
    将角度标准化到 0-2π 范围

    Args:
        angle: 角度（弧度）

    Returns:
        标准化后的角度
    """
    while angle < 0:
        angle += 2 * math.pi
    while angle >= 2 * math.pi:
        angle -= 2 * math.pi
    return angle


def random_in_range(min_val: float, max_val: float) -> float:
    """
    在指定范围内生成随机数

    Args:
        min_val: 最小值
        max_val: 最大值

    Returns:
        随机数
    """
    return random.uniform(min_val, max_val)


def random_int(min_val: int, max_val: int) -> int:
    """
    在指定范围内生成随机整数

    Args:
        min_val: 最小值
        max_val: 最大值

    Returns:
        随机整数
    """
    return random.randint(min_val, max_val)


def chance(probability: float) -> bool:
    """
    根据概率返回True或False

    Args:
        probability: 概率 (0-1)

    Returns:
        是否命中
    """
    return random.random() < probability
