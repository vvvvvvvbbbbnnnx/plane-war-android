"""
飞机大战 - 碰撞检测系统

使用空间分区优化碰撞检测性能
"""
from collections import defaultdict

from core.entity import Entity


class SpatialHash:
    """
    空间哈希碰撞检测

    将游戏空间划分为网格，只检测同一网格内的实体碰撞
    """

    def __init__(self, cell_size: int = 64):
        """
        初始化空间哈希

        Args:
            cell_size: 网格单元大小
        """
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], set[Entity]] = defaultdict(set)

        self._entity_count = 0

    def clear(self) -> None:
        """清空所有网格"""
        self.cells.clear()
        self._entity_count = 0

    def _get_cell(self, x: float, y: float) -> tuple[int, int]:
        """
        获取坐标所在的网格

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            (cell_x, cell_y) 网格坐标
        """
        return (int(x // self.cell_size), int(y // self.cell_size))

    def _get_cells_for_rect(self, x: float, y: float, w: float, h: float) -> list[tuple[int, int]]:
        """
        获取矩形覆盖的所有网格

        Args:
            x: 矩形左下角X坐标
            y: 矩形左下角Y坐标
            w: 矩形宽度
            h: 矩形高度

        Returns:
            网格坐标列表
        """
        cells = []
        start_x, start_y = self._get_cell(x, y)
        end_x, end_y = self._get_cell(x + w, y + h)


        for cx in range(start_x, end_x + 1):
            for cy in range(start_y, end_y + 1):
                cells.append((cx, cy))

        return cells

    def insert(self, entity: Entity) -> None:
        """
        将实体插入空间哈希

        Args:
            entity: 要插入的实体
        """
        bounds = entity.get_bounds()
        cells = self._get_cells_for_rect(*bounds)

        for cell in cells:
            self.cells[cell].add(entity)

        self._entity_count += 1

    def remove(self, entity: Entity) -> None:
        """
        从空间哈希中移除实体

        Args:
            entity: 要移除的实体
        """
        bounds = entity.get_bounds()
        cells = self._get_cells_for_rect(*bounds)

        for cell in cells:
            self.cells[cell].discard(entity)

        self._entity_count -= 1

    def get_nearby(self, entity: Entity) -> set[Entity]:
        """
        获取实体附近的潜在碰撞对象

        Args:
            entity: 查询实体

        Returns:
            附近的实体集合
        """
        nearby = set()
        bounds = entity.get_bounds()
        cells = self._get_cells_for_rect(*bounds)

        for cell in cells:
            nearby.update(self.cells[cell])

        # 移除自身
        nearby.discard(entity)

        return nearby

    def get_entity_count(self) -> int:
        """获取实体总数"""
        return self._entity_count

    def get_all_entities(self) -> set[Entity]:
        """
        获取所有实体

        Returns:
            所有实体的集合
        """
        all_entities = set()
        for cell_entities in self.cells.values():
            all_entities.update(cell_entities)
        return all_entities

    def __iter__(self):
        """迭代所有实体"""
        return iter(self.get_all_entities())


class CollisionSystem:
    """
    碰撞检测系统

    磀测不同类型实体之间的碰撞
    """

    def __init__(self, cell_size: int = 64):
        """
        初始化碰撞系统

        Args:
            cell_size: 空间哈希单元大小
        """
        self.spatial_hash = SpatialHash(cell_size)

        # 碰撞组配置
        # (type1, type2) -> callback
        self._collision_groups: dict[tuple[str, str], callable] = {}

        # 类型预映射：entity_type -> [(other_type, callback)]
        # 注册时双向登记，check_collisions 时按实体类型 O(1) 查找，
        # 取代之前对每对 nearby 实体遍历全部 _collision_groups 的 O(N×M) 扫描。
        self._type_index: dict[str, list[tuple[str, callable]]] = {}

    def register_collision_group(
        self,
        type1: str,
        type2: str,
        callback: callable
    ) -> None:
        """
        注册碰撞组

        Args:
            type1: 第一种实体类型
            type2: 第二种实体类型
            callback: 碰撞回调函数 (entity1, entity2)
        """
        self._collision_groups[(type1, type2)] = callback
        # 双向登记：type1 实体遇到 type2，type2 实体遇到 type1，都能查到。
        # 当 type1 == type2（同类型碰撞，如敌机互撞）时只登记一次，避免重复触发。
        self._type_index.setdefault(type1, []).append((type2, callback))
        if type2 != type1:
            self._type_index.setdefault(type2, []).append((type1, callback))

    def clear(self) -> None:
        """清空碰撞系统"""
        self.spatial_hash.clear()

    def update(self, entities: list[Entity]) -> None:
        """
        更新碰撞检测

        Args:
            entities: 所有活动实体列表
        """
        # 清空并重新插入所有实体
        self.spatial_hash.clear()

        for entity in entities:
            if entity.active:
                self.spatial_hash.insert(entity)

    def check_collisions(self) -> list[tuple[Entity, Entity]]:
        """
        检测所有碰撞

        Returns:
            [(entity1, entity2), ...] 碰撞对列表
        """
        collisions = []
        checked_pairs: set[frozenset] = set()  # 单向去重

        for entity in self.spatial_hash:
            if not entity.active:
                continue

            # 当前实体没有注册任何碰撞关系，直接跳过（避免无谓的 nearby 查询）
            groups = self._type_index.get(entity.entity_type)
            if not groups:
                continue

            nearby = self.spatial_hash.get_nearby(entity)

            for other in nearby:
                if not other.active:
                    continue

                # frozenset 单向去重：{a,b} 与 {b,a} 相同，一次 add 即可
                pair = frozenset((id(entity), id(other)))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                # 按实体类型 O(1) 查找该实体参与的碰撞组
                for other_type, callback in groups:
                    if other.entity_type == other_type:
                        # 确定回调参数顺序：以 (type1, type2) 注册顺序为准，
                        # 使 callback(a, b) 的 a/b 与注册时一致。
                        if self._collision_groups.get(
                            (entity.entity_type, other_type)
                        ) is callback:
                            a, b = entity, other
                        else:
                            a, b = other, entity
                        if a.collides_with(b):
                            collisions.append((a, b))
                            callback(a, b)

        return collisions

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'entity_count': self.spatial_hash.get_entity_count(),
            'collision_groups': len(self._collision_groups),
        }
