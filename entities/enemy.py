"""
飞机大战 - 敌机 (多移动模式 + 被击闪白)

设计要点
--------
* 数值属性（血量/速度/分数/尺寸）来自 ``config.enemies``（EnemyConfig）。
* 移动模式与颜色为「显示层」属性，不在 EnemyConfig 中，故由 ``TYPE_CONFIGS``
  提供；``_setup_type`` 优先读 config，``TYPE_CONFIGS`` 兼作兜底与移动模式来源。
* 玩家引用通过 ``_get_player`` 延迟导入 ``core.game`` 获取，避免反向穿透 widget 树。
"""
import math

from kivy.graphics import Color as GColor
from kivy.graphics import Line
from kivy.graphics import Rectangle as GRect
from kivy.properties import NumericProperty, StringProperty

from config.settings import get_config
from core.entity import Entity
from utils.helpers import chance
from utils.screen import screen


class Enemy(Entity):
    enemy_type = StringProperty('normal')
    health = NumericProperty(1)
    score = NumericProperty(100)
    move_pattern = StringProperty('straight')

    # 各敌机类型的显示/移动配置（数值属性以 config.enemies 为准，此处提供移动模式与兜底值）
    TYPE_CONFIGS = {
        'normal': {
            'width_ratio': 0.08, 'height_ratio': 0.05,
            'health': 1, 'speed': 3.0, 'score': 100,
            'shoot_prob': 0.005, 'color': (1, 0.2, 0.2),
            'move': 'sine',
        },
        'fast': {
            'width_ratio': 0.06, 'height_ratio': 0.04,
            'health': 1, 'speed': 5.0, 'score': 150,
            'shoot_prob': 0.008, 'color': (0.8, 0.4, 1),
            'move': 'zigzag',
        },
        'tank': {
            'width_ratio': 0.11, 'height_ratio': 0.06,
            'health': 3, 'speed': 2.0, 'score': 300,
            'shoot_prob': 0.01, 'color': (0.4, 0.4, 0.4),
            'move': 'charge',
        },
    }

    def __init__(self, enemy_type: str = 'normal', **kwargs):
        super().__init__(**kwargs)
        self.entity_type = 'enemy'
        self.enemy_type = enemy_type
        self._setup_type()
        image_map = {
            'normal': 'enemy_normal.png',
            'fast': 'enemy_fast.png',
            'tank': 'enemy_tank.png',
        }
        self._image_loaded = self.setup_image(image_map.get(enemy_type, 'enemy_normal.png'))
        self._hitbox_scale = 0.8
        self._move_timer = 0.0
        self._flash_timer = 0.0
        self._move_amplitude = screen.rel_w(0.06)
        self._move_frequency = 2.0 + (1.5 if enemy_type == 'fast' else 0)
        # 确保移动模式从 TYPE_CONFIGS 读取（config 路径无 move 字段）
        tc = self.TYPE_CONFIGS.get(enemy_type, {})
        if 'move' in tc and self.move_pattern == 'straight':
            self.move_pattern = tc['move']

    def _setup_type(self) -> None:
        config = get_config()
        if self.enemy_type in config.enemies:
            ec = config.enemies[self.enemy_type]
            self.set_size_rel(ec.width_ratio, ec.height_ratio)
            self.health = ec.health
            self._base_speed = ec.speed
            self.score = ec.score
            self._shoot_prob = ec.shoot_probability
            self._color = (
                ec.health / 3, 0.2 + (0.3 if self.enemy_type == 'fast' else 0),
                0.2 + (0.8 if self.enemy_type == 'tank' else 0),
            )
        else:
            tc = self.TYPE_CONFIGS.get(self.enemy_type, self.TYPE_CONFIGS['normal'])
            self.set_size_rel(tc['width_ratio'], tc['height_ratio'])
            self.health = tc['health']
            self._base_speed = tc['speed']
            self.score = tc['score']
            self._shoot_prob = tc['shoot_prob']
            self._color = tc['color']
            self.move_pattern = tc.get('move', 'straight')
        self.speed = screen.scale_value(self._base_speed)
        self.velocity_y = -self.speed

    def update(self, dt: float) -> None:
        super().update(dt)
        self._move_timer += dt
        if self._flash_timer > 0:
            self._flash_timer -= dt
        self._apply_move_pattern(dt)
        if self.y < -self.height * 2:
            self.active = False

    def _get_player(self):
        """获取玩家引用（延迟导入 game 单例，避免与 core.game 循环导入）。

        取代此前 ``self.parent.game.player`` 的反向穿透：不再依赖 widget 树结构，
        且在敌机尚未挂载到根 widget 时也能正确获取玩家。
        """
        from core.game import get_game
        return get_game().player

    def _apply_move_pattern(self, dt: float) -> None:
        """根据移动模式更新横向/纵向速度。

        支持三种模式：
        * sine    — 正弦摆动（普通敌机）
        * zigzag  — 左右折返（快速敌机）
        * charge  — 先缓后快下冲并追踪玩家 X 坐标（坦克敌机）
        """
        p = self.move_pattern
        t = self._move_timer

        if p == 'sine':
            offset = math.sin(t * self._move_frequency * 5) * self._move_amplitude
            self.velocity_x = offset * 8

        elif p == 'zigzag':
            period = 1.0 / self._move_frequency
            phase_t = t % period
            if phase_t < period / 2:
                self.velocity_x = -self.speed * 2.5
            else:
                self.velocity_x = self.speed * 2.5

        elif p == 'charge':
            # 屏幕上半段缓速接近，过线后加速下冲
            if self.y > screen.real_height * 0.65:
                self.velocity_y = -self.speed * 0.5
            else:
                self.velocity_y = -self.speed * 2.5
            # 追踪玩家横向位置（限速，避免瞬移）
            player = self._get_player()
            if player:
                dx = player.center_x - self.center_x
                self.velocity_x = max(-self.speed, min(self.speed, dx * 0.8))

        # 边界钳制：撞墙后折返方向，避免飞出屏幕
        if self.x < 0:
            self.x = 0
            if p == 'zigzag':
                self.velocity_x = abs(self.velocity_x)
        elif self.x > screen.real_width - self.width:
            self.x = screen.real_width - self.width
            if p == 'zigzag':
                self.velocity_x = -abs(self.velocity_x)

    def should_shoot(self) -> bool:
        """按射击概率随机决定是否开火（每帧独立判定）。"""
        return chance(self._shoot_prob)

    def take_damage(self, amount: int = 1) -> bool:
        """承受伤害：扣血，血量归零则标记失活；存活时触发短暂闪白特效。

        Returns:
            是否死亡（active 被置为 False）
        """
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.active = False
            return True
        self._flash_timer = 0.06
        return False

    def draw(self) -> None:
        """绘制敌机：优先使用贴图；无贴图时按类型用线条/矩形绘制矢量外形。

        被击中时（``_flash_timer > 0``）叠加白色半透明矩形作为闪白反馈。
        """
        flash = self._flash_timer > 0
        color = (1, 1, 1) if flash else getattr(self, '_color', (1, 0.2, 0.2))
        if self._image_loaded:
            if flash:
                self.canvas.after.clear()
                with self.canvas.after:
                    GColor(1, 1, 1, 0.5)
                    GRect(pos=self.pos, size=self.size)
            return
        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            GColor(*color)
            if self.enemy_type == 'normal':
                pts = [(self.center_x, self.y), (self.x, self.top - h*0.25),
                       (self.center_x, self.top - h*0.5), (self.right, self.top - h*0.25)]
                Line(points=pts, width=screen.dp(2), close=True)
            elif self.enemy_type == 'fast':
                pts = [(self.center_x, self.y), (self.x, self.top),
                       (self.center_x, self.top - h*0.25), (self.right, self.top)]
                Line(points=pts, width=screen.dp(2), close=True)
            elif self.enemy_type == 'tank':
                GRect(pos=(self.x+w*0.1, self.y+h*0.1), size=(w*0.8, h*0.8))
                GColor(0.6, 0.2, 0.2)
                GRect(pos=(self.x+w*0.2, self.y+h*0.2), size=(w*0.6, h*0.6))

    def reset(self) -> None:
        super().reset()
        self._setup_type()
        self._move_timer = 0.0
        self._flash_timer = 0.0
