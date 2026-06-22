"""Tests for core/pool.py - ObjectPool and MultiTypePool."""
from core.pool import MultiTypePool, ObjectPool, PoolStats


class Counter:
    """Simple test object with reset."""
    _counter = 0

    def __init__(self):
        Counter._counter += 1
        self.id = Counter._counter
        self.active = False
        self.value = 0

    def reset(self):
        self.active = False
        self.value = 0


def make_counter():
    return Counter()


class TestObjectPool:
    def test_pool_pre_creates_objects(self):
        pool = ObjectPool(make_counter, initial_size=5)
        assert pool.get_stats().current_pooled == 5

    def test_acquire_returns_object(self):
        pool = ObjectPool(make_counter, initial_size=2)
        obj = pool.acquire()
        assert isinstance(obj, Counter)

    def test_acquire_calls_reset(self):
        pool = ObjectPool(make_counter, initial_size=1)
        obj = pool.acquire(value=42)
        obj.value = 99
        pool.release(obj)
        obj2 = pool.acquire()
        assert obj2.value == 0  # reset was called

    def test_acquire_sets_attributes(self):
        pool = ObjectPool(make_counter, initial_size=1)
        obj = pool.acquire(value=42)
        assert obj.value == 42

    def test_release_returns_to_pool(self):
        pool = ObjectPool(make_counter, initial_size=1)
        obj = pool.acquire()
        assert pool.get_stats().current_active == 1
        pool.release(obj)
        assert pool.get_stats().current_active == 0

    def test_release_then_acquire_gives_same_object(self):
        pool = ObjectPool(make_counter, initial_size=1)
        obj1 = pool.acquire()
        obj_id = id(obj1)
        pool.release(obj1)
        obj2 = pool.acquire()
        assert id(obj2) == obj_id

    def test_release_all(self):
        pool = ObjectPool(make_counter, initial_size=3)
        for _ in range(3):
            pool.acquire()
        assert len(pool) == 3
        pool.release_all()
        assert len(pool) == 0

    def test_stats_accurate(self):
        pool = ObjectPool(make_counter, initial_size=2)
        obj1 = pool.acquire()
        pool.acquire()
        stats = pool.get_stats()
        assert stats.current_active == 2
        pool.release(obj1)
        stats = pool.get_stats()
        assert stats.current_active == 1

    def test_max_size_limit(self):
        """max_size 满时拒绝 release，对象保留在 active 列表而非被丢弃"""
        import pytest
        pool = ObjectPool(make_counter, initial_size=2, max_size=2)
        obj1 = pool.acquire()
        obj2 = pool.acquire()
        pool.release(obj1)
        pool.release(obj2)
        # 池已满（2 个），obj3 release 应被拒绝并抛 RuntimeWarning
        obj3 = pool.acquire()
        with pytest.warns(RuntimeWarning):
            pool.release(obj3)
        stats = pool.get_stats()
        # 被拒绝后对象仍在 active 中
        assert stats.current_pooled <= 2
        assert stats.current_active == 1
        assert obj3 in pool

    def test_release_non_contained_no_error(self):
        pool = ObjectPool(make_counter, initial_size=1)
        fake = Counter()
        pool.release(fake)  # should not raise

    def test_clear_empties_pool(self):
        pool = ObjectPool(make_counter, initial_size=5)
        pool.acquire()
        pool.clear()
        assert len(pool) == 0
        assert pool.get_stats().current_pooled == 0

    def test_iter_yields_active(self):
        pool = ObjectPool(make_counter, initial_size=2)
        objs = [pool.acquire() for _ in range(2)]
        active = list(pool)
        assert len(active) == 2
        assert objs[0] in active

    def test_contains_checks_active(self):
        pool = ObjectPool(make_counter, initial_size=1)
        obj = pool.acquire()
        assert obj in pool
        pool.release(obj)
        assert obj not in pool

    def test_get_active_returns_copy(self):
        pool = ObjectPool(make_counter, initial_size=2)
        pool.acquire()
        active = pool.get_active()
        assert len(active) == 1


class TestMultiTypePool:
    def test_register_creates_pool(self):
        mtp = MultiTypePool()
        pool = mtp.register('test', make_counter, initial_size=3)
        assert pool is not None
        assert mtp.get_pool('test') is pool

    def test_acquire_wrong_type_raises(self):
        mtp = MultiTypePool()
        import pytest
        with pytest.raises(KeyError):
            mtp.acquire('nonexistent')

    def test_acquire_release_different_types(self):
        mtp = MultiTypePool()
        mtp.register('a', make_counter, initial_size=2)
        mtp.register('b', make_counter, initial_size=2)

        obj_a = mtp.acquire('a')
        obj_b = mtp.acquire('b')
        assert obj_a is not None
        assert obj_b is not None

        mtp.release('a', obj_a)
        mtp.release('b', obj_b)

    def test_release_all_single_type(self):
        mtp = MultiTypePool()
        mtp.register('x', make_counter, initial_size=3)
        for _ in range(3):
            mtp.acquire('x')
        mtp.release_all('x')
        assert len(mtp.get_pool('x')) == 0

    def test_release_all_all_types(self):
        mtp = MultiTypePool()
        mtp.register('a', make_counter, initial_size=2)
        mtp.register('b', make_counter, initial_size=2)
        mtp.acquire('a')
        mtp.acquire('b')
        mtp.release_all()
        assert len(mtp.get_pool('a')) == 0
        assert len(mtp.get_pool('b')) == 0

    def test_get_all_stats(self):
        mtp = MultiTypePool()
        mtp.register('s1', make_counter, initial_size=2)
        stats = mtp.get_all_stats()
        assert 's1' in stats
        assert isinstance(stats['s1'], PoolStats)

    def test_clear_all(self):
        mtp = MultiTypePool()
        mtp.register('c', make_counter, initial_size=5)
        mtp.acquire('c')
        mtp.clear_all()
        assert len(mtp.get_pool('c')) == 0

    def test_get_pool_nonexistent(self):
        mtp = MultiTypePool()
        assert mtp.get_pool('ghost') is None
