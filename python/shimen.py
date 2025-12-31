import time
from tools import Task, DeviceController


class Shimen(Task):
    def __init__(self, device_id, max_rounds=None):
        """
        初始化师门任务
        
        参数:
            device_id: 设备ID
            max_rounds: 最大执行轮数，None 表示无限循环（用于单独运行），数字表示执行指定轮数后结束（用于任务队列）
        """
        self.device_id = device_id
        self.controller = DeviceController(device_id)
        self._task_count = 0
        self._max_rounds = max_rounds  # None 表示无限循环

    def run(self):
                    # 任务主循环
        while self._is_running:
            self._task_count += 1

            self.controller.写入日志(f'[{self.device_id}] 师门任务 - 第 {self._task_count} 轮')
            
            # 模拟任务步骤
            self._执行师门步骤()
            
            # 检查是否达到最大轮数
            if self._max_rounds and self._task_count >= self._max_rounds:
                self.controller.写入日志(f'[{self.device_id}] 师门任务达到最大轮数 ({self._max_rounds})，自动结束')
                break
            
            # 检查是否还在运行
            if not self._is_running:
                break
            
            # 等待一段时间再执行下一轮（模拟任务间隔）
            for _ in range(10):  # 每0.5秒检查一次，总共5秒
                if not self._is_running:
                    break
                time.sleep(0.5)
        
        self.controller.写入日志(f'[{self.device_id}] 师门任务已结束，共完成 {self._task_count} 轮')
    
    def _执行师门步骤(self):
        """执行师门任务的具体步骤"""
        if not self._is_running:
            return
        
        # 步骤1: 截图
        print(f'[{self.device_id}] 师门任务 - 步骤1: 截图')
        # screenshot_path = self.截图()
        # if screenshot_path:
        #     print(f'[{self.device_id}] 截图成功: {screenshot_path}')
        time.sleep(0.5)
        
        if not self._is_running:
            return
        
        # 步骤2: 查找NPC
        print(f'[{self.device_id}] 师门任务 - 步骤2: 查找NPC')
        time.sleep(0.5)
        
        if not self._is_running:
            return
        
        # 步骤3: 点击NPC
        print(f'[{self.device_id}] 师门任务 - 步骤3: 点击NPC')
        time.sleep(0.5)
        
        if not self._is_running:
            return
        
        # 步骤4: 完成任务
        print(f'[{self.device_id}] 师门任务 - 步骤4: 完成任务')
        time.sleep(0.5)
        



