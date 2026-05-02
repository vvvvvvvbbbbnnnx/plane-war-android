"""Tests for systems/save.py - SaveManager."""

from systems.save import SaveManager


class TestSaveManager:
    def test_new_save_has_no_save(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        assert not sm.has_save()

    def test_save_and_load_game_state(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.save_game({'score': 100, 'level': 3})
        loaded = sm.load_game()
        assert loaded['score'] == 100
        assert loaded['level'] == 3

    def test_has_save_after_save(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.save_game({'score': 50})
        assert sm.has_save()

    def test_delete_save(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.save_game({'score': 50})
        sm.delete_save()
        assert not sm.has_save()

    def test_get_high_score_default(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        assert sm.get_high_score() == 0

    def test_save_high_score_new(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.save_high_score(1000)
        assert sm.get_high_score() == 1000

    def test_save_high_score_only_higher(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.save_high_score(2000)
        sm.save_high_score(1500)
        assert sm.get_high_score() == 2000

    def test_save_high_score_overwrite_lower_ignored(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.save_high_score(500)
        sm.save_high_score(300)
        assert sm.get_high_score() == 500

    def test_save_load_settings(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.save_settings({'music_volume': 0.5, 'sound_enabled': False})
        settings = sm.load_settings()
        assert settings['music_volume'] == 0.5
        assert settings['sound_enabled'] is False

    def test_load_settings_defaults(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        settings = sm.load_settings()
        assert settings['music_volume'] == 0.7
        assert settings['sound_enabled'] is True

    def test_load_achievements_empty(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        assert sm.load_achievements() == {}

    def test_save_load_achievements(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.save_achievements({'first_blood': {'unlocked': True, 'progress': 1}})
        achievements = sm.load_achievements()
        assert achievements['first_blood']['unlocked'] is True

    def test_load_statistics_defaults(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        stats = sm.load_statistics()
        assert stats['total_games'] == 0
        assert stats['total_score'] == 0

    def test_update_statistics_accumulates(self, temp_json_path):
        sm = SaveManager(filename=temp_json_path)
        sm.update_statistics({'total_score': 100})
        sm.update_statistics({'total_score': 50})
        sm.update_statistics({'total_games': 1})
        stats = sm.load_statistics()
        assert stats['total_score'] == 150
        assert stats['total_games'] == 1
