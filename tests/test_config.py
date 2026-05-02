"""Tests for config/settings.py - GameConfig, level generation, JSON roundtrip."""
import os
import tempfile

from config.settings import (
    BossConfig,
    EnemyConfig,
    GameConfig,
    PlayerConfig,
    PowerUpConfig,
    get_config,
)


class TestPlayerConfig:
    def test_defaults(self):
        cfg = PlayerConfig()
        assert cfg.max_health == 3
        assert cfg.max_weapon_level == 3
        assert cfg.base_speed == 8.0
        assert cfg.invincible_time == 2.0
        assert cfg.shield_duration == 5.0
        assert cfg.max_bombs == 5
        assert cfg.max_lives == 5


class TestEnemyConfig:
    def test_defaults(self):
        cfg = EnemyConfig()
        assert cfg.health == 1
        assert cfg.speed == 3.0
        assert cfg.score == 100


class TestBossConfig:
    def test_defaults(self):
        cfg = BossConfig()
        assert cfg.base_health == 20
        assert cfg.health_per_level == 10
        assert cfg.base_score == 1000


class TestPowerUpConfig:
    def test_default_types(self):
        cfg = PowerUpConfig()
        assert 'health' in cfg.types
        assert 'weapon' in cfg.types
        assert 'shield' in cfg.types
        assert 'bomb' in cfg.types
        assert cfg.drop_rate == 0.15


class TestGameConfig:
    def test_default_creation(self):
        cfg = GameConfig()
        assert cfg.design_width == 720
        assert cfg.design_height == 1280
        assert cfg.shoot_cooldown == 0.15
        assert cfg.double_tap_threshold == 0.3

    def test_enemy_types_generated(self):
        cfg = GameConfig()
        assert 'normal' in cfg.enemies
        assert 'fast' in cfg.enemies
        assert 'tank' in cfg.enemies

    def test_levels_generated(self):
        cfg = GameConfig()
        assert len(cfg.levels) == 10

    def test_level_1_has_only_normal(self):
        cfg = GameConfig()
        lvl = cfg.get_level(1)
        assert lvl.enemy_types == ['normal']

    def test_level_10_has_all_types(self):
        cfg = GameConfig()
        lvl = cfg.get_level(10)
        assert 'normal' in lvl.enemy_types
        assert 'fast' in lvl.enemy_types
        assert 'tank' in lvl.enemy_types

    def test_level_progression_enemies_to_kill(self):
        cfg = GameConfig()
        assert cfg.get_level(1).enemies_to_kill == 15
        assert cfg.get_level(10).enemies_to_kill == 60

    def test_level_progression_spawn_rate_decreases(self):
        cfg = GameConfig()
        assert cfg.get_level(1).spawn_rate > cfg.get_level(10).spawn_rate

    def test_get_level_clamps_low(self):
        cfg = GameConfig()
        lvl = cfg.get_level(0)
        assert lvl.level == 1

    def test_get_level_clamps_high(self):
        cfg = GameConfig()
        lvl = cfg.get_level(999)
        assert lvl.level == 10

    def test_get_level_mid_range(self):
        cfg = GameConfig()
        lvl = cfg.get_level(5)
        assert lvl.level == 5

    def test_boss_health_per_level(self):
        cfg = GameConfig()
        lvl1 = cfg.get_level(1)
        lvl10 = cfg.get_level(10)
        assert lvl10.boss_health > lvl1.boss_health

    def test_singleton_returns_same_instance(self):
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2


class TestGameConfigJSON:
    def test_json_roundtrip(self):
        cfg = GameConfig()
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        try:
            cfg.save(path)
            loaded = GameConfig.load(path)
            assert loaded.design_width == cfg.design_width
            assert loaded.shoot_cooldown == cfg.shoot_cooldown
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_load_nonexistent_returns_default(self):
        cfg = GameConfig.load('/nonexistent/path/config.json')
        assert isinstance(cfg, GameConfig)
        assert len(cfg.levels) == 10

    def test_save_and_load_player_config(self):
        cfg = GameConfig()
        cfg.player.max_health = 5
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        try:
            cfg.save(path)
            loaded = GameConfig.load(path)
            assert loaded.player.max_health == 5
        finally:
            if os.path.exists(path):
                os.remove(path)
