from typing import Dict, Callable, Optional, Any
import time
# 基于流程的状态机
# 需要梳理流程,按照流程一步步编写,并且如果有任何意外情况,都要添加逻辑进行处理

# 基于界面的状态机
# 无脑,写个上下文,在哪个界面根据上下文需要做什么事即可

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





class InterfaceStateMachine:
    def __init__(self):
        self._states: Dict[str, Callable] = {}
        self._current_interface: Optional[str] = None
        self._previous_interface: Optional[str] = None
        self._is_running: bool = False
        self._context: Dict[str, Any] = {}  # 上下文信息
        
        # 界面识别函数（需要用户实现）
        self._interface_recognizer: Optional[Callable] = None
        
    def set_recognizer(self, recognizer: Callable) -> 'InterfaceStateMachine':
        """设置界面识别函数"""
        self._interface_recognizer = recognizer
        return self
        
    def on(self, interface: str, handler: Callable) -> 'InterfaceStateMachine':
        """注册界面处理函数"""
        self._states[interface] = handler
        return self
        
    def state(self, name):
        """装饰器：直接注册界面处理函数"""
        def decorator(func):
            self._states[name] = func
            return func
        return decorator
        
    def start(self) -> Any:
        """启动状态机"""
        self._is_running = True
        
        while self._is_running:
            try:
                # 识别当前界面
                detected_interface = self._interface_recognizer()
                
                # 如果检测到界面变化
                if detected_interface != self._current_interface:
                    self._previous_interface = self._current_interface
                    self._current_interface = detected_interface
                    
                
                # 如果当前界面有注册处理函数
                if self._current_interface in self._states:
                    handler = self._states[self._current_interface]
                    
                    # 执行界面处理函数，传入当前上下文
                    result = handler(self._context)
                    
                    # 处理函数可以返回False表示需要保持当前界面状态
                    # 或者返回新的上下文数据
                    if isinstance(result, dict):
                        self._context.update(result)
                    elif result is False:
                        # 处理函数返回False，表示操作失败或需要重试
                        print(f"界面 {self._current_interface} 处理失败")
                
                # 短暂延迟，避免CPU占用过高
                # time.sleep(1)
                
            except Exception as e:
                print(f"状态机运行异常: {e}")
                self.stop()
            
    def stop(self):
        """停止状态机"""
        self._is_running = False
        
        