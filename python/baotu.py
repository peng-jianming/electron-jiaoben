import time
from tools import DeviceController


class Baotu(DeviceController):
    def __init__(self, device_id):
        super().__init__(device_id)
        self._is_running = False
        self._task_count = 0

    def start(self):
        """开始宝图任务"""
        self._is_running = True
        self._task_count = 0
        print(f'[{self.device_id}] 开始宝图任务')
        
        try:
            # 任务主循环
            while self._is_running:
                self._task_count += 1
                print(f'[{self.device_id}] 宝图任务 - 第 {self._task_count} 轮')
                
                # 模拟任务步骤
                self._执行宝图步骤()
                
                # 检查是否还在运行
                if not self._is_running:
                    break
                
                # 等待一段时间再执行下一轮（模拟任务间隔）
                for _ in range(10):  # 每0.5秒检查一次，总共5秒
                    if not self._is_running:
                        break
                    time.sleep(0.5)
            
            print(f'[{self.device_id}] 宝图任务已结束，共完成 {self._task_count} 轮')
            
        except Exception as e:
            print(f'[{self.device_id}] 宝图任务执行出错: {e}')
            import traceback
            traceback.print_exc()
        finally:
            self._is_running = False
    
    def _执行宝图步骤(self):
        """执行宝图任务的具体步骤"""
        if not self._is_running:
            return
        
        # 步骤1: 截图
        print(f'[{self.device_id}] 宝图任务 - 步骤1: 截图')
        # screenshot_path = self.截图()
        # if screenshot_path:
        #     print(f'[{self.device_id}] 截图成功: {screenshot_path}')
        time.sleep(0.5)
        
        if not self._is_running:
            return
        
        # 步骤2: 查找宝图NPC
        print(f'[{self.device_id}] 宝图任务 - 步骤2: 查找宝图NPC')
        time.sleep(0.5)
        
        if not self._is_running:
            return
        
        # 步骤3: 点击NPC
        print(f'[{self.device_id}] 宝图任务 - 步骤3: 点击NPC')
        time.sleep(0.5)
        
        if not self._is_running:
            return
        
        # 步骤4: 挖宝图
        print(f'[{self.device_id}] 宝图任务 - 步骤4: 挖宝图')
        time.sleep(0.5)
        
    def stop(self):
        """停止宝图任务"""
        if self._is_running:
            print(f'[{self.device_id}] 正在停止宝图任务...')
            self._is_running = False
        else:
            print(f'[{self.device_id}] 宝图任务未在运行')



