# -*- coding: utf-8 -*-
"""
飞机大战 - Pygame 增强版 v2.0
控制: WASD/方向键移动, 空格射击, B炸弹, P暂停, R重新开始
"""
import pygame
import random
import math
import json
import os
from sys import exit

# ==================== 常量 ====================
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 700
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 100)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 150, 50)
PURPLE = (200, 100, 255)
CYAN = (50, 255, 255)
DARK_BLUE = (20, 30, 60)
GRAY = (100, 100, 100)

# 游戏配置
PLAYER_SPEED = 6
BULLET_SPEED = 12
ENEMY_BULLET_SPEED = 5
POWERUP_DROP_CHANCE = 0.15
INVINCIBLE_FRAMES = 60

# 存档文件
SAVE_FILE = "plane_war_save.json"


# ==================== 工具函数 ====================
def load_high_score():
    """加载最高分"""
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
    except:
        pass
    return 0


def save_high_score(score):
    """保存最高分"""
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump({'high_score': score}, f)
    except:
        pass


# ==================== 子弹类 ====================
class Bullet(pygame.sprite.Sprite):
    """玩家子弹"""
    def __init__(self, x, y, vx=0, vy=-BULLET_SPEED):
        super().__init__()
        self.vx = vx
        self.vy = vy
        self.image = pygame.Surface((6, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, CYAN, (0, 0, 6, 18))
        pygame.draw.ellipse(self.image, WHITE, (1, 2, 4, 14))
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.bottom < 0:
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    """敌方子弹"""
    def __init__(self, x, y, vx=0, vy=ENEMY_BULLET_SPEED):
        super().__init__()
        self.vx = vx
        self.vy = vy
        self.image = pygame.Surface((8, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, RED, (0, 0, 8, 12))
        pygame.draw.ellipse(self.image, ORANGE, (2, 2, 4, 8))
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ==================== 玩家类 ====================
class Player(pygame.sprite.Sprite):
    """玩家飞机"""
    def __init__(self):
        super().__init__()
        self.image = self._create_image()
        self.rect = self.image.get_rect(centerx=SCREEN_WIDTH // 2, bottom=SCREEN_HEIGHT - 50)
        self.speed = PLAYER_SPEED
        self.health = 100
        self.max_health = 100
        self.weapon_level = 1
        self.shield = 0
        self.bombs = 1
        self.invincible = 0

    def _create_image(self):
        """绘制飞机图像"""
        surf = pygame.Surface((50, 60), pygame.SRCALPHA)
        # 机身
        points = [(25, 0), (5, 45), (25, 35), (45, 45)]
        pygame.draw.polygon(surf, CYAN, points)
        # 机翼
        pygame.draw.polygon(surf, BLUE, [(5, 45), (0, 55), (15, 50)])
        pygame.draw.polygon(surf, BLUE, [(45, 45), (50, 55), (35, 50)])
        # 驾驶舱
        pygame.draw.ellipse(surf, WHITE, (18, 15, 14, 20))
        pygame.draw.ellipse(surf, CYAN, (20, 17, 10, 16))
        # 引擎火焰
        pygame.draw.rect(surf, ORANGE, (20, 45, 10, 8))
        return surf

    def shoot(self, bullets_group):
        """射击"""
        if self.weapon_level == 1:
            bullets_group.add(Bullet(self.rect.centerx, self.rect.top))
        elif self.weapon_level == 2:
            bullets_group.add(Bullet(self.rect.centerx - 10, self.rect.top))
            bullets_group.add(Bullet(self.rect.centerx + 10, self.rect.top))
        else:
            bullets_group.add(Bullet(self.rect.centerx, self.rect.top))
            bullets_group.add(Bullet(self.rect.centerx - 15, self.rect.top + 10, -1, -11))
            bullets_group.add(Bullet(self.rect.centerx + 15, self.rect.top + 10, 1, -11))

    def update(self, keys):
        """更新位置"""
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            if self.rect.top > SCREEN_HEIGHT // 2:
                self.rect.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            if self.rect.bottom < SCREEN_HEIGHT:
                self.rect.y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            if self.rect.left > 0:
                self.rect.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            if self.rect.right < SCREEN_WIDTH:
                self.rect.x += self.speed

        if self.invincible > 0:
            self.invincible -= 1

    def draw(self, surface):
        """绘制玩家（含无敌闪烁和护盾）"""
        if self.invincible <= 0 or self.invincible % 6 >= 3:
            surface.blit(self.image, self.rect)
            if self.shield > 0:
                pygame.draw.circle(surface, CYAN, self.rect.center, 35, 2)


# ==================== 敌机类 ====================
class Enemy(pygame.sprite.Sprite):
    """敌机"""
    TYPES = {
        'normal': {'health': 1, 'speed': (2, 4), 'score': 10, 'size': (35, 35)},
        'fast': {'health': 1, 'speed': (5, 7), 'score': 15, 'size': (25, 30)},
        'tank': {'health': 5, 'speed': (1, 2), 'score': 30, 'size': (50, 45)},
    }

    def __init__(self, enemy_type='normal'):
        super().__init__()
        self.type = enemy_type
        props = self.TYPES[enemy_type]
        self.image = self._create_image(props['size'])
        self.rect = self.image.get_rect(
            x=random.randint(0, SCREEN_WIDTH - props['size'][0]),
            y=random.randint(-150, -50)
        )
        self.health = props['health']
        self.speed = random.uniform(*props['speed'])
        self.score = props['score']

    def _create_image(self, size):
        """绘制敌机图像"""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        w, h = size
        cx, cy = w // 2, h // 2

        if self.type == 'normal':
            points = [(cx, h), (0, 5), (cx, h//3), (w, 5)]
            pygame.draw.polygon(surf, RED, points)
            pygame.draw.polygon(surf, ORANGE, [(cx, h-5), (w//4, h//4), (w-w//4, h//4)])
        elif self.type == 'fast':
            points = [(cx, h), (0, 0), (cx, h//3), (w, 0)]
            pygame.draw.polygon(surf, PURPLE, points)
        else:  # tank
            pygame.draw.rect(surf, GRAY, (5, 10, w-10, h-15), border_radius=5)
            pygame.draw.rect(surf, RED, (10, 15, w-20, h-25), border_radius=3)
            pygame.draw.rect(surf, ORANGE, (cx-5, 0, 10, 15))
        return surf

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ==================== Boss类 ====================
class Boss(pygame.sprite.Sprite):
    """Boss"""
    def __init__(self, level):
        super().__init__()
        self.level = level
        self.size = 120 + level * 10
        self.image = self._create_image()
        self.rect = self.image.get_rect(centerx=SCREEN_WIDTH // 2, y=-150)
        self.max_health = 100 + level * 50
        self.health = self.max_health
        self.speed = 2
        self.direction = 1
        self.shoot_timer = 0
        self.phase = 0
        self.target_y = 80

    def _create_image(self):
        """绘制Boss图像"""
        surf = pygame.Surface((self.size, self.size // 2), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (80, 0, 0), (0, 0, self.size, self.size // 2))
        pygame.draw.ellipse(surf, RED, (10, 5, self.size - 20, self.size // 2 - 10))
        pygame.draw.rect(surf, (100, 0, 0), (0, self.size // 4, self.size, self.size // 4))
        pygame.draw.circle(surf, YELLOW, (self.size // 2, self.size // 4), 20)
        pygame.draw.circle(surf, WHITE, (self.size // 2, self.size // 4), 10)
        return surf

    def update(self):
        """更新Boss位置"""
        if self.phase == 0:
            self.rect.y += 2
            if self.rect.y >= self.target_y:
                self.phase = 1
        else:
            self.rect.x += self.speed * self.direction
            if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
                self.direction *= -1

    def shoot(self, bullets_group):
        """Boss射击"""
        self.shoot_timer += 1
        if self.shoot_timer >= 30:
            self.shoot_timer = 0
            if self.health > self.max_health * 0.5:
                bullets_group.add(EnemyBullet(self.rect.centerx, self.rect.bottom))
            else:
                # 狂暴模式：散射
                for angle in range(-30, 31, 15):
                    rad = math.radians(90 + angle)
                    vx = math.cos(rad) * ENEMY_BULLET_SPEED
                    vy = math.sin(rad) * ENEMY_BULLET_SPEED
                    bullets_group.add(EnemyBullet(self.rect.centerx, self.rect.bottom, vx, vy))


# ==================== 道具类 ====================
class PowerUp(pygame.sprite.Sprite):
    """道具"""
    TYPES = ['health', 'weapon', 'shield', 'bomb']

    def __init__(self, x, y, power_type=None):
        super().__init__()
        self.type = power_type or random.choice(self.TYPES)
        self.image = self._create_image()
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2

    def _create_image(self):
        """绘制道具图像"""
        surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        if self.type == 'health':
            pygame.draw.circle(surf, GREEN, (15, 15), 12)
            pygame.draw.rect(surf, WHITE, (12, 8, 6, 14))
            pygame.draw.rect(surf, WHITE, (8, 12, 14, 6))
        elif self.type == 'weapon':
            pygame.draw.polygon(surf, YELLOW, [(15, 2), (5, 28), (15, 20), (25, 28)])
        elif self.type == 'shield':
            pygame.draw.circle(surf, CYAN, (15, 15), 12, 3)
        else:  # bomb
            pygame.draw.circle(surf, ORANGE, (15, 15), 10)
            pygame.draw.rect(surf, WHITE, (13, 3, 4, 8))
        return surf

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ==================== 爆炸类 ====================
class Explosion(pygame.sprite.Sprite):
    """爆炸效果"""
    def __init__(self, x, y, size='small'):
        super().__init__()
        self.size = {'small': 30, 'medium': 60, 'large': 100}.get(size, 30)
        self.image = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.frame = 0
        self.max_frames = 15

    def update(self):
        self.frame += 1
        if self.frame < self.max_frames:
            progress = self.frame / self.max_frames
            radius = int(self.size * progress)
            alpha = int(255 * (1 - progress))
            self.image.fill((0, 0, 0, 0))
            for i, color in enumerate([(255, 200, 50), (255, 100, 0), (255, 50, 0)]):
                r = max(1, radius - i * 5)
                pygame.draw.circle(self.image, (*color, alpha), (self.size, self.size), r)
        else:
            self.kill()


# ==================== 星星背景 ====================
class Star:
    """背景星星"""
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.5, 2)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(100, 255)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        color = (self.brightness,) * 3
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)


# ==================== 游戏主类 ====================
class Game:
    """游戏主类"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("飞机大战 - 增强版 v2.0")
        self.clock = pygame.time.Clock()

        # 字体
        try:
            self.font = pygame.font.SysFont('microsoftyahei', 24)
            self.font_large = pygame.font.SysFont('microsoftyahei', 36)
        except:
            self.font = pygame.font.Font(None, 28)
            self.font_large = pygame.font.Font(None, 42)

        # 最高分
        self.high_score = load_high_score()

        # 初始化
        self.reset()

    def reset(self):
        """重置游戏"""
        # 精灵组
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()

        # 玩家
        self.player = Player()
        self.all_sprites.add(self.player)

        # 背景
        self.stars = [Star() for _ in range(100)]

        # Boss
        self.boss = None
        self.boss_spawned = False

        # 游戏状态
        self.score = 0
        self.level = 1
        self.enemies_killed = 0
        self.level_goal = 20
        self.game_over = False
        self.paused = False
        self.state = 'menu'  # menu, playing, gameover

        # 计时器
        self.shoot_timer = 0
        self.enemy_timer = 0

    def spawn_enemy(self):
        """生成敌机"""
        if self.boss:
            return

        self.enemy_timer += 1
        if self.enemy_timer >= 60:
            self.enemy_timer = 0
            if self.level == 1:
                enemy_type = 'normal'
            elif self.level == 2:
                enemy_type = random.choices(['normal', 'fast'], [0.7, 0.3])[0]
            else:
                enemy_type = random.choices(['normal', 'fast', 'tank'], [0.5, 0.3, 0.2])[0]
            enemy = Enemy(enemy_type)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

    def spawn_boss(self):
        """生成Boss"""
        if self.enemies_killed >= self.level_goal and not self.boss_spawned:
            self.boss = Boss(self.level)
            self.all_sprites.add(self.boss)
            self.boss_spawned = True

    def use_bomb(self):
        """使用炸弹"""
        if self.player.bombs <= 0:
            return

        self.player.bombs -= 1
        for enemy in self.enemies:
            self.score += enemy.score
            self.explosions.add(Explosion(enemy.rect.centerx, enemy.rect.centery, 'medium'))
            if random.random() < POWERUP_DROP_CHANCE:
                self.powerups.add(PowerUp(enemy.rect.centerx, enemy.rect.centery))
        self.enemies.empty()

        if self.boss:
            self.boss.health -= 20

    def handle_collisions(self):
        """处理碰撞"""
        # 玩家子弹击中敌机
        hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, True)
        for enemy, bullets in hits.items():
            enemy.health -= len(bullets)
            if enemy.health <= 0:
                self.score += enemy.score
                self.enemies_killed += 1
                self.explosions.add(Explosion(enemy.rect.centerx, enemy.rect.centery))
                if random.random() < POWERUP_DROP_CHANCE:
                    powerup = PowerUp(enemy.rect.centerx, enemy.rect.centery)
                    self.powerups.add(powerup)
                enemy.kill()

        # 玩家子弹击中Boss
        if self.boss:
            hits = pygame.sprite.spritecollide(self.boss, self.player_bullets, True)
            self.boss.health -= len(hits)
            if self.boss.health <= 0:
                self.score += 500 * self.level
                self.explosions.add(Explosion(self.boss.rect.centerx, self.boss.rect.centery, 'large'))
                self.boss.kill()
                self.boss = None
                self.level += 1
                self.enemies_killed = 0
                self.level_goal = 20 + self.level * 5
                self.boss_spawned = False
                self.player.weapon_level = min(3, self.player.weapon_level + 1)

        # 敌机撞击玩家
        if self.player.invincible <= 0:
            hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
            if hits:
                self.player.health -= 20 * len(hits)
                self.player.invincible = INVINCIBLE_FRAMES
                self.explosions.add(Explosion(self.player.rect.centerx, self.player.rect.centery))

            # 敌方子弹击中玩家
            hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
            if hits:
                self.player.health -= 10 * len(hits)
                self.player.invincible = INVINCIBLE_FRAMES

            # Boss撞击玩家
            if self.boss and self.boss.phase == 1 and self.player.rect.colliderect(self.boss.rect):
                self.player.health -= 30
                self.player.invincible = INVINCIBLE_FRAMES

        # 道具
        hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for powerup in hits:
            if powerup.type == 'health':
                self.player.health = min(self.player.max_health, self.player.health + 30)
            elif powerup.type == 'weapon':
                self.player.weapon_level = min(3, self.player.weapon_level + 1)
            elif powerup.type == 'shield':
                self.player.shield = 50
            elif powerup.type == 'bomb':
                self.player.bombs = min(3, self.player.bombs + 1)

    def update(self):
        """更新游戏状态"""
        if self.state != 'playing' or self.paused:
            return

        # 自动射击
        self.shoot_timer += 1
        if self.shoot_timer >= 10:
            self.shoot_timer = 0
            self.player.shoot(self.player_bullets)

        # 生成敌机和Boss
        self.spawn_enemy()
        self.spawn_boss()

        # Boss射击
        if self.boss and self.boss.phase == 1:
            self.boss.shoot(self.enemy_bullets)

        # 更新精灵
        self.player.update(pygame.key.get_pressed())
        self.enemies.update()
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.powerups.update()
        self.explosions.update()
        if self.boss:
            self.boss.update()

        # 更新背景
        for star in self.stars:
            star.update()

        # 碰撞检测
        self.handle_collisions()

        # 检查游戏结束
        if self.player.health <= 0:
            self.state = 'gameover'
            if self.score > self.high_score:
                self.high_score = self.score
                save_high_score(self.high_score)

    def draw_ui(self):
        """绘制UI"""
        # 血条
        pygame.draw.rect(self.screen, GRAY, (10, 10, 150, 12), border_radius=3)
        health_ratio = max(0, self.player.health) / self.player.max_health
        color = GREEN if health_ratio > 0.5 else YELLOW if health_ratio > 0.25 else RED
        pygame.draw.rect(self.screen, color, (10, 10, 150 * health_ratio, 12), border_radius=3)

        # 分数和关卡
        self.screen.blit(self.font.render(f"分数: {self.score}", True, WHITE), (SCREEN_WIDTH - 120, 10))
        self.screen.blit(self.font.render(f"关卡: {self.level}", True, WHITE), (SCREEN_WIDTH - 120, 40))
        self.screen.blit(self.font.render(f"炸弹: {self.player.bombs}", True, ORANGE), (SCREEN_WIDTH - 120, 70))
        self.screen.blit(self.font.render(f"武器: Lv.{self.player.weapon_level}", True, YELLOW), (10, 40))

        # 最高分
        self.screen.blit(self.font.render(f"最高: {self.high_score}", True, (150, 150, 150)), (10, 70))

        # 关卡进度
        if not self.boss:
            progress = self.enemies_killed / self.level_goal
            pygame.draw.rect(self.screen, GRAY, (SCREEN_WIDTH // 2 - 50, 10, 100, 8), border_radius=4)
            pygame.draw.rect(self.screen, GREEN, (SCREEN_WIDTH // 2 - 50, 10, 100 * progress, 8), border_radius=4)

        # Boss血条
        if self.boss:
            bar_width = 200
            x = (SCREEN_WIDTH - bar_width) // 2
            pygame.draw.rect(self.screen, GRAY, (x, 10, bar_width, 15), border_radius=5)
            ratio = max(0, self.boss.health) / self.boss.max_health
            pygame.draw.rect(self.screen, RED, (x, 10, bar_width * ratio, 15), border_radius=5)

    def draw_menu(self):
        """绘制菜单"""
        # 标题
        title = self.font_large.render("飞机大战", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))

        # 最高分
        high = self.font.render(f"最高分: {self.high_score}", True, YELLOW)
        self.screen.blit(high, (SCREEN_WIDTH // 2 - high.get_width() // 2, 280))

        # 开始提示
        start = self.font.render("按 SPACE 开始游戏", True, WHITE)
        self.screen.blit(start, (SCREEN_WIDTH // 2 - start.get_width() // 2, 400))

        # 控制说明
        controls = [
            "WASD / 方向键 - 移动",
            "SPACE - 射击 (自动)",
            "B - 炸弹",
            "P - 暂停",
        ]
        for i, text in enumerate(controls):
            ctrl = self.font.render(text, True, (150, 150, 150))
            self.screen.blit(ctrl, (SCREEN_WIDTH // 2 - ctrl.get_width() // 2, 480 + i * 30))

    def draw_gameover(self):
        """绘制游戏结束"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        # 游戏结束
        text = self.font_large.render("游戏结束", True, RED)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 250))

        # 分数
        score = self.font.render(f"得分: {self.score}", True, WHITE)
        self.screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 320))

        # 新纪录
        if self.score >= self.high_score:
            new_record = self.font.render("新纪录!", True, YELLOW)
            self.screen.blit(new_record, (SCREEN_WIDTH // 2 - new_record.get_width() // 2, 360))

        # 重新开始
        restart = self.font.render("按 R 重新开始 / 按 ESC 返回菜单", True, WHITE)
        self.screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, 420))

    def draw(self):
        """绘制画面"""
        # 背景
        self.screen.fill(DARK_BLUE)
        for star in self.stars:
            star.draw(self.screen)

        if self.state == 'menu':
            self.draw_menu()
        else:
            # 游戏元素
            self.powerups.draw(self.screen)
            self.player_bullets.draw(self.screen)
            self.enemy_bullets.draw(self.screen)
            self.enemies.draw(self.screen)
            if self.boss:
                self.screen.blit(self.boss.image, self.boss.rect)
            self.player.draw(self.screen)
            self.explosions.draw(self.screen)

            # UI
            self.draw_ui()

            # 暂停
            if self.paused:
                text = self.font_large.render("暂停中 - 按 P 继续", True, WHITE)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))

            # 游戏结束
            if self.state == 'gameover':
                self.draw_gameover()

        pygame.display.flip()

    def run(self):
        """主循环"""
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == 'playing':
                            self.state = 'menu'
                            self.reset()
                        else:
                            running = False

                    if self.state == 'menu':
                        if event.key == pygame.K_SPACE:
                            self.state = 'playing'

                    elif self.state == 'playing':
                        if event.key == pygame.K_p:
                            self.paused = not self.paused
                        elif event.key == pygame.K_b and not self.paused:
                            self.use_bomb()
                        elif event.key == pygame.K_r:
                            self.reset()
                            self.state = 'playing'

                    elif self.state == 'gameover':
                        if event.key == pygame.K_r:
                            self.reset()
                            self.state = 'playing'

            self.update()
            self.draw()

        pygame.quit()
        exit()


# ==================== 入口 ====================
if __name__ == '__main__':
    game = Game()
    game.run()
