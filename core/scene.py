"""
飞机大战 - 场景管理器

管理游戏场景的切换和生命周期
"""
from enum import Enum
from typing import Optional

from kivy.uix.floatlayout import FloatLayout


class SceneState(Enum):
    """场景状态"""
    CREATED = 'created'
    ENTERING = 'entering'
    ACTIVE = 'active'
    EXITING = 'exiting'
    DESTROYED = 'destroyed'


class Scene(FloatLayout):
    """
    场景基类

    所有游戏场景（菜单、游戏、暂停等）都继承自此类
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = SceneState.CREATED
        self.scene_manager: Optional[SceneManager] = None

    def on_enter(self) -> None:
        """进入场景时调用"""
        self.state = SceneState.ENTERING

    def on_enter_complete(self) -> None:
        """进入动画完成后调用"""
        self.state = SceneState.ACTIVE

    def on_exit(self) -> None:
        """退出场景时调用"""
        self.state = SceneState.EXITING

    def on_exit_complete(self) -> None:
        """退出动画完成后调用"""
        self.state = SceneState.DESTROYED

    def update(self, dt: float) -> None:
        """
        更新场景

        Args:
            dt: 时间增量
        """
        pass

    def pause(self) -> None:
        """暂停场景"""
        pass

    def resume(self) -> None:
        """恢复场景"""
        pass


class SceneManager:
    """
    场景管理器

    管理场景的创建、切换、销毁
    """

    def __init__(self, initial_scene: Optional[Scene] = None):
        """
        初始化场景管理器

        Args:
            initial_scene: 初始场景
        """
        self.current_scene: Optional[Scene] = None
        self.scenes: dict[str, Scene] = {}
        self._scene_stack: list = []

        # 场景切换动画
        self._transition_duration = 0.3
        self._transitioning = False

        if initial_scene:
            self.push_scene(initial_scene)

    def register_scene(self, name: str, scene: Scene) -> None:
        """
        注册场景

        Args:
            name: 场景名称
            scene: 场景实例
        """
        scene.scene_manager = self
        self.scenes[name] = scene

    def get_scene(self, name: str) -> Optional[Scene]:
        """获取已注册的场景"""
        return self.scenes.get(name)

    def push_scene(self, scene: Scene) -> None:
        """
        推入新场景

        Args:
            scene: 新场景
        """
        if self._transitioning:
            return

        # 暂停当前场景
        if self.current_scene:
            self.current_scene.pause()

        # 添加新场景
        scene.scene_manager = self
        self._scene_stack.append(scene)
        self.add_widget(scene)

        # 退出旧场景
        if self.current_scene:
            self.current_scene.on_exit()

        # 切换到新场景
        old_scene = self.current_scene
        self.current_scene = scene
        scene.on_enter()

        # 开始过渡动画
        self._start_transition(old_scene, scene)

    def pop_scene(self) -> Optional[Scene]:
        """
        弹出当前场景

        Returns:
            被弹出的场景
        """
        if len(self._scene_stack) <= 1 or self._transitioning:
            return None

        # 退出当前场景
        current = self._scene_stack.pop()
        current.on_exit()

        # 恢复上一个场景
        if self._scene_stack:
            self.current_scene = self._scene_stack[-1]
            self.current_scene.resume()

        # 移除旧场景
        self.remove_widget(current)
        current.on_exit_complete()

        return current

    def replace_scene(self, scene: Scene) -> None:
        """
        替换当前场景

        Args:
            scene: 新场景
        """
        if self._transitioning:
            return

        # 退出当前场景
        if self.current_scene:
            self.current_scene.on_exit()
            old_scene = self._scene_stack.pop() if self._scene_stack else None
        else:
            old_scene = None

        # 添加新场景
        scene.scene_manager = self
        self._scene_stack.append(scene)
        self.add_widget(scene)

        # 切换到新场景
        self.current_scene = scene
        scene.on_enter()

        # 开始过渡动画
        self._start_transition(old_scene, scene)

    def _start_transition(self, old_scene: Optional[Scene], new_scene: Scene) -> None:
        """
        开始过渡动画

        Args:
            old_scene: 旧场景
            new_scene: 新场景
        """
        self._transitioning = True

        # 新场景从右侧滑入
        new_scene.x = self.width

        # 动画
        from kivy.animation import Animation
        anim = Animation(x=0, duration=self._transition_duration, t='out_quad')

        def on_complete(*args):
            self._transitioning = False
            new_scene.on_enter_complete()

            if old_scene:
                self.remove_widget(old_scene)
                old_scene.on_exit_complete()

        anim.bind(on_complete=on_complete)
        anim.start(new_scene)

    def update(self, dt: float) -> None:
        """
        更新当前场景

        Args:
            dt: 时间增量
        """
        if self.current_scene and self.current_scene.state == SceneState.ACTIVE:
            self.current_scene.update(dt)

    def clear_all(self) -> None:
        """清空所有场景"""
        for scene in self._scene_stack:
            scene.on_exit()
            self.remove_widget(scene)
            scene.on_exit_complete()

        self._scene_stack.clear()
        self.current_scene = None
