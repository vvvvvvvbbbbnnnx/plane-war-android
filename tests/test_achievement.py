"""Tests for systems/achievement.py - AchievementManager."""

from kivy.storage.jsonstore import JsonStore

import systems.achievement as achievement_module
import systems.save as save_module
from systems.achievement import Achievement


class TestAchievement:
    def test_achievement_defaults(self):
        a = Achievement('test', 'Test', 'A test achievement')
        assert a.id == 'test'
        assert a.unlocked is False
        assert a.progress == 0
        assert a.target == 1

    def test_hidden_achievement(self):
        a = Achievement('secret', 'Secret', 'Hidden', hidden=True)
        assert a.hidden is True


class TestAchievementManager:
    """Each test uses a fresh temp-file save so singletons don't leak."""

    @staticmethod
    def _fresh_am(temp_json_path):
        """Create an AchievementManager backed by a clean temp save file."""
        old_store = save_module.save_manager.store
        save_module.save_manager.store = JsonStore(temp_json_path)
        save_module.save_manager.clear_all()
        achievement_module.AchievementManager._instance = None
        am = achievement_module.AchievementManager()
        save_module.save_manager.store = old_store
        return am

    def test_increment_first_blood_unlocks(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        result = am.check_achievement('first_blood', 1)
        assert result is True
        assert am.get_achievement('first_blood').unlocked is True

    def test_increment_partial_no_unlock(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        result = am.increment_achievement('killer_10', 5)
        assert result is False
        assert am.get_achievement('killer_10').progress == 5
        assert am.get_achievement('killer_10').unlocked is False

    def test_increment_reaches_target_unlocks(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        am.increment_achievement('killer_10', 10)
        assert am.get_achievement('killer_10').unlocked is True

    def test_already_unlocked_no_change(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        am.unlock_achievement('first_blood')
        result = am.increment_achievement('first_blood', 100)
        assert result is False

    def test_direct_unlock(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        result = am.unlock_achievement('boss_first')
        assert result is True
        assert am.get_achievement('boss_first').unlocked is True

    def test_direct_unlock_already_unlocked(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        am.unlock_achievement('boss_first')
        result = am.unlock_achievement('boss_first')
        assert result is False

    def test_unlock_callback_invoked(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        called = []

        def cb(achievement):
            called.append(achievement.id)

        am.on_unlock = cb
        am.unlock_achievement('first_blood')
        assert 'first_blood' in called

    def test_get_unlocked_count(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        assert am.get_unlocked_count() == 0
        am.unlock_achievement('first_blood')
        am.unlock_achievement('killer_10')
        assert am.get_unlocked_count() == 2

    def test_get_total_count(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        assert am.get_total_count() > 0

    def test_visible_excludes_hidden(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        visible = am.get_visible_achievements()
        assert all(not a.hidden for a in visible)

    def test_hidden_visible_when_unlocked(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        am.unlock_achievement('no_damage')
        visible = am.get_visible_achievements()
        no_damage = [a for a in visible if a.id == 'no_damage']
        assert len(no_damage) == 1

    def test_reset_all(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        am.unlock_achievement('first_blood')
        am.unlock_achievement('killer_10')
        am.reset_all()
        assert am.get_unlocked_count() == 0

    def test_nonexistent_achievement(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        assert am.get_achievement('nonexistent') is None
        assert am.increment_achievement('nonexistent') is False

    def test_get_progress(self, temp_json_path):
        am = self._fresh_am(temp_json_path)
        am.increment_achievement('killer_100', 25)
        progress = am.get_progress('killer_100')
        assert progress == 0.25
