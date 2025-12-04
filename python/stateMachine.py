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


# 示例配置类，模拟你的配置对象
class Config:
    """模拟配置类"""
    class 跳过:
        @staticmethod
        def 查找并点击():
            # 模拟逻辑：假设这里返回False，不跳过
            print("执行: 跳过.查找并点击() -> False")
            return False
            
    class 使用:
        @staticmethod
        def 查找并点击():
            # 模拟逻辑：假设这里返回False
            print("执行: 使用.查找并点击() -> False")
            return False
            
    class 上交:
        @staticmethod
        def 查找并点击():
            # 模拟逻辑：假设这里返回False
            print("执行: 上交.查找并点击() -> False")
            return False
            
    class 弹框_购买:
        @staticmethod
        def 查找并点击():
            # 模拟逻辑：假设这里返回False
            print("执行: 弹框_购买.查找并点击() -> False")
            return False
            
    class 摆摊弹框_购买:
        @staticmethod
        def 查找并点击():
            # 模拟逻辑：假设这里返回True
            print("执行: 摆摊弹框_购买.查找并点击() -> True")
            return True


# 测试代码
if __name__ == "__main__":
    # 创建配置实例
    配置 = Config()
    

    
    # 注册状态处理函数（链式调用）
    result = StateMachine() \
       .on('1', lambda: 配置.跳过.查找并点击() and '1' or '2') \
       .on('2', lambda: 配置.使用.查找并点击() and '1' or '3') \
       .on('3', lambda: 配置.上交.查找并点击() and '1' or '4') \
       .on('4', lambda: 配置.弹框_购买.查找并点击() and '1' or '5') \
       .on('5', lambda: 配置.摆摊弹框_购买.查找并点击() and '8' or '1') \
       .start('1')
    # 启动状态机，开始时代码会在这里"暂停"直到状态机执行完毕

    
    # 状态机执行完毕后，代码继续往下执行
    print(f"状态机执行完成，返回结果: '{result}'")
    print("代码继续执行...")