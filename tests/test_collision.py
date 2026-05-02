"""Tests for systems/collision.py - SpatialHash and CollisionSystem."""
from systems.collision import CollisionSystem, SpatialHash


class MockEntity:
    """Minimal mock entity for collision testing (avoids Kivy Widget dependency)."""

    def __init__(self, x=0, y=0, w=32, h=32, entity_type='test', active=True):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.entity_type = entity_type
        self.active = active

    def get_bounds(self):
        return (self.x, self.y, self.width, self.height)

    def collides_with(self, other):
        ax1, ay1, aw, ah = self.get_bounds()
        bx1, by1, bw, bh = other.get_bounds()
        return not (
            ax1 + aw <= bx1 or
            bx1 + bw <= ax1 or
            ay1 + ah <= by1 or
            by1 + bh <= ay1
        )

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other


class TestSpatialHash:
    def test_insert_and_get_nearby(self):
        sh = SpatialHash(cell_size=64)
        e1 = MockEntity(10, 10, 32, 32)
        e2 = MockEntity(20, 20, 32, 32)
        sh.insert(e1)
        sh.insert(e2)
        nearby = sh.get_nearby(e1)
        assert e2 in nearby

    def test_self_excluded_from_nearby(self):
        sh = SpatialHash(cell_size=64)
        e1 = MockEntity(10, 10, 32, 32)
        sh.insert(e1)
        nearby = sh.get_nearby(e1)
        assert e1 not in nearby

    def test_remove(self):
        sh = SpatialHash(cell_size=64)
        e1 = MockEntity(10, 10, 32, 32)
        sh.insert(e1)
        sh.remove(e1)
        nearby = sh.get_nearby(MockEntity(10, 10, 32, 32))
        assert e1 not in nearby

    def test_entity_count(self):
        sh = SpatialHash(cell_size=64)
        e1 = MockEntity(0, 0, 32, 32)
        e2 = MockEntity(100, 100, 32, 32)
        sh.insert(e1)
        sh.insert(e2)
        assert sh.get_entity_count() == 2

    def test_clear(self):
        sh = SpatialHash(cell_size=64)
        sh.insert(MockEntity(0, 0, 32, 32))
        sh.clear()
        assert sh.get_entity_count() == 0

    def test_get_all_entities(self):
        sh = SpatialHash(cell_size=64)
        e1 = MockEntity(10, 10, 32, 32)
        e2 = MockEntity(200, 200, 32, 32)
        sh.insert(e1)
        sh.insert(e2)
        all_entities = sh.get_all_entities()
        assert e1 in all_entities
        assert e2 in all_entities

    def test_far_entities_not_nearby(self):
        sh = SpatialHash(cell_size=64)
        e1 = MockEntity(0, 0, 32, 32)
        e2 = MockEntity(500, 500, 32, 32)
        sh.insert(e1)
        sh.insert(e2)
        nearby = sh.get_nearby(e1)
        assert e2 not in nearby

    def test_iter_yields_all(self):
        sh = SpatialHash(cell_size=64)
        e1 = MockEntity(0, 0, 32, 32)
        sh.insert(e1)
        entities = list(sh)
        assert e1 in entities


class TestCollisionSystem:
    def test_register_collision_group(self):
        cs = CollisionSystem()
        cs.register_collision_group('bullet', 'enemy', lambda a, b: None)
        assert cs.get_stats()['collision_groups'] == 1

    def test_collision_detected(self):
        cs = CollisionSystem()
        callback_called = []

        def on_collision(a, b):
            callback_called.append((a, b))

        cs.register_collision_group('bullet', 'enemy', on_collision)

        bullet = MockEntity(50, 50, 8, 12, entity_type='bullet')
        enemy = MockEntity(40, 40, 32, 32, entity_type='enemy')

        cs.update([bullet, enemy])
        cs.check_collisions()
        assert len(callback_called) == 1

    def test_no_collision_when_separated(self):
        cs = CollisionSystem()
        callback_called = []

        cs.register_collision_group('bullet', 'enemy', lambda a, b: callback_called.append(1))

        bullet = MockEntity(0, 0, 8, 12, entity_type='bullet')
        enemy = MockEntity(200, 200, 32, 32, entity_type='enemy')

        cs.update([bullet, enemy])
        cs.check_collisions()
        assert len(callback_called) == 0

    def test_inactive_entity_not_checked(self):
        cs = CollisionSystem()
        callback_called = []

        cs.register_collision_group('bullet', 'enemy', lambda a, b: callback_called.append(1))

        bullet = MockEntity(50, 50, 8, 12, entity_type='bullet', active=False)
        enemy = MockEntity(40, 40, 32, 32, entity_type='enemy')

        cs.update([bullet, enemy])
        cs.check_collisions()
        assert len(callback_called) == 0

    def test_pair_deduplication(self):
        cs = CollisionSystem()
        callback_called = []

        cs.register_collision_group('test', 'test', lambda a, b: callback_called.append(1))

        e1 = MockEntity(50, 50, 32, 32, entity_type='test')
        e2 = MockEntity(60, 60, 32, 32, entity_type='test')

        cs.update([e1, e2])
        cs.check_collisions()
        # Each pair should only trigger once
        assert len(callback_called) == 1

    def test_get_stats(self):
        cs = CollisionSystem()
        cs.register_collision_group('a', 'b', lambda a, b: None)
        cs.register_collision_group('c', 'd', lambda a, b: None)
        stats = cs.get_stats()
        assert stats['collision_groups'] == 2
