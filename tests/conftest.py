"""Shared test fixtures for plane-war-android."""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Kivy headless before any tests run
os.environ['KIVY_NO_ARGS'] = '1'
os.environ['KIVY_NO_CONSOLELOG'] = '1'


@pytest.fixture
def temp_json_path():
    """Create a temporary JSON file path for save tests."""
    fd, path = tempfile.mkstemp(suffix='.json', prefix='plane_war_test_')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset global singletons between tests."""
    from config.settings import GameConfig
    from systems.achievement import AchievementManager
    from systems.save import SaveManager

    # Reset achievement manager state
    AchievementManager._instance = None

    # Reset save manager
    SaveManager._instance = None

    # Reset config singleton
    GameConfig._instance = None

    yield

    AchievementManager._instance = None
    SaveManager._instance = None
    GameConfig._instance = None
