"""
飞机大战 - 对象池

提供通用的对象池实现，用于减少对象创建/销毁的开销。
"""
import warnings
from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar('T')


@dataclass
class PoolStats:
    """对象池统计信息"""
    total_created: int = 0
    total_acquired: int = 0
    total_released: int = 0
    current_active: int = 0
    current_pooled: int = 0


class ObjectPool(Generic[T]):
    """
    通用对象池

    通过预创建和复用对象来减少内存分配和垃圾回收的开销。

    Attributes:
        factory: 对象工厂函数
        initial_size: 初始池大小
        max_size: 最大池大小（0表示无限制）
        on_acquire: 获取对象时的回调
        on_release: 释放对象时的回调
    """

    def __init__(
        self,
        factory: Callable[[], T],
        initial_size: int = 50,
        max_size: int = 0,
        on_acquire: Optional[Callable[[T], None]] = None,
        on_release: Optional[Callable[[T], None]] = None
    ):
        """
        初始化对象池

        Args:
            factory: 创建新对象的工厂函数
            initial_size: 初始预创建的对象数量
            max_size: 最大池大小，0表示无限制
            on_acquire: 获取对象时的回调函数
            on_release: 释放对象时的回调函数
        """
        self.factory = factory
        self.max_size = max_size
        self.on_acquire = on_acquire
        self.on_release = on_release

        # 对象存储
        self._pool: list[T] = []
        self._active: list[T] = []

        # 统计信息
        self._stats = PoolStats()

        # 预创建对象
        for _ in range(initial_size):
            obj = self._create_object()
            self._pool.append(obj)

        self._stats.current_pooled = len(self._pool)

    def _create_object(self) -> T:
        """创建新对象"""
        obj = self.factory()
        self._stats.total_created += 1
        return obj

    def acquire(self, **kwargs) -> T:
        """
        从池中获取一个对象

        Args:
            **kwargs: 设置对象属性的参数

        Returns:
            可用的对象
        """
        # 从池中取出或创建新对象
        if self._pool:
            obj = self._pool.pop()
            self._stats.current_pooled -= 1
        else:
            obj = self._create_object()

        # 重置对象状态
        if hasattr(obj, 'reset'):
            obj.reset()

        # 设置属性
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        # 添加到活动列表
        self._active.append(obj)

        # 更新统计
        self._stats.total_acquired += 1
        self._stats.current_active += 1

        # 回调
        if self.on_acquire:
            self.on_acquire(obj)

        return obj

    def release(self, obj: T) -> None:
        """
        将对象释放回池中

        Args:
            obj: 要释放的对象
        """
        if obj not in self._active:
            return

        # 检查是否超过最大大小：满时拒绝 release（对象保留在 active 列表中），
        # 避免之前"先移除 active 再丢弃"导致对象既脱离 active 又不入 pool、
        # 下次 acquire 重新创建造成的内存抖动与外部悬空引用。
        if self.max_size > 0 and len(self._pool) >= self.max_size:
            warnings.warn(
                f"ObjectPool({self.factory}) 已达 max_size={self.max_size}，"
                f"release 被拒绝（对象保留在 active 列表）",
                RuntimeWarning,
                stacklevel=2,
            )
            return

        # 从活动列表移除
        self._active.remove(obj)
        self._stats.current_active -= 1

        # 回调
        if self.on_release:
            self.on_release(obj)

        # 放回池中
        self._pool.append(obj)
        self._stats.current_pooled += 1
        self._stats.total_released += 1

    def release_all(self) -> None:
        """释放所有活动对象"""
        for obj in self._active[:]:
            self.release(obj)

    def get_active(self) -> list[T]:
        """获取所有活动对象"""
        return self._active.copy()

    def get_stats(self) -> PoolStats:
        """获取统计信息"""
        return self._stats

    def clear(self) -> None:
        """清空对象池"""
        self._pool.clear()
        self._active.clear()
        self._stats.current_pooled = 0
        self._stats.current_active = 0

    def __len__(self) -> int:
        """返回活动对象数量"""
        return len(self._active)

    def __iter__(self):
        """迭代活动对象"""
        return iter(self._active)

    def __contains__(self, obj: T) -> bool:
        """检查对象是否在活动列表中"""
        return obj in self._active


class MultiTypePool:
    """
    多类型对象池

    管理多种类型对象的池集合
    """

    def __init__(self):
        self._pools: dict = {}

    def register(
        self,
        type_name: str,
        factory: Callable[[], T],
        initial_size: int = 50,
        max_size: int = 0,
        on_acquire: Optional[Callable[[T], None]] = None,
        on_release: Optional[Callable[[T], None]] = None
    ) -> ObjectPool[T]:
        """
        注册一个类型的对象池

        Args:
            type_name: 类型名称
            factory: 对象工厂
            initial_size: 初始大小
            max_size: 最大大小
            on_acquire: 获取回调
            on_release: 释放回调

        Returns:
            创建的对象池
        """
        pool = ObjectPool(
            factory=factory,
            initial_size=initial_size,
            max_size=max_size,
            on_acquire=on_acquire,
            on_release=on_release
        )
        self._pools[type_name] = pool
        return pool

    def acquire(self, type_name: str, **kwargs) -> T:
        """
        从指定类型的池中获取对象

        Args:
            type_name: 类型名称
            **kwargs: 对象属性

        Returns:
            对象实例
        """
        if type_name not in self._pools:
            raise KeyError(f"未注册的对象池类型: {type_name}")
        return self._pools[type_name].acquire(**kwargs)

    def release(self, type_name: str, obj: T) -> None:
        """
        将对象释放回指定类型的池

        Args:
            type_name: 类型名称
            obj: 对象实例
        """
        if type_name in self._pools:
            self._pools[type_name].release(obj)

    def release_all(self, type_name: str = None) -> None:
        """
        释放所有对象

        Args:
            type_name: 类型名称，None表示所有类型
        """
        if type_name:
            if type_name in self._pools:
                self._pools[type_name].release_all()
        else:
            for pool in self._pools.values():
                pool.release_all()

    def get_pool(self, type_name: str) -> Optional[ObjectPool]:
        """获取指定类型的对象池"""
        return self._pools.get(type_name)

    def get_all_stats(self) -> dict:
        """获取所有池的统计信息"""
        return {name: pool.get_stats() for name, pool in self._pools.items()}

    def clear_all(self) -> None:
        """清空所有池"""
        for pool in self._pools.values():
            pool.clear()
