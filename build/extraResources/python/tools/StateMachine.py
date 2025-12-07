from typing import Dict, Callable, Optional, Any

class StateMachine:
    def __init__(self):
        self._states: Dict[str, Callable] = {}
        self._current_state: Optional[str] = None
        self._result: Any = None
        self._is_running: bool = False

    def state(self, name):
        """装饰器：直接注册状态处理函数"""
        def decorator(func):
            self._states[name] = func
            return func
        return decorator
        
    def on(self, state: str, handler: Callable) -> 'StateMachine':
        """注册状态处理函数"""
        self._states[state] = handler
        return self
        
    def start(self, initial_state: str) -> Any:
        """启动状态机"""
        self._current_state = initial_state
        self._is_running = True
        
        while self._is_running and self._current_state is not None:
            # 如果当前状态已注册
            if self._current_state in self._states:
                # 执行状态处理函数
                handler = self._states[self._current_state]
                next_state = handler()
                
                # 如果返回了下一个状态
                if next_state is not None:
                    self._current_state = str(next_state)
                else:
                    self._result = self._current_state
                    self._is_running = False
            else:
                # 状态未注册，结束状态机
                self._result = self._current_state
                self._is_running = False
                
        return self._result
        
    def stop(self):
        """停止状态机"""
        self._is_running = False
        
    def get_current_state(self) -> Optional[str]:
        """获取当前状态"""
        return self._current_state
