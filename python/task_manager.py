import threading
import time
from typing import Dict, Optional
from baotu import Baotu
from shimen import Shimen


class TaskManager:
    """多线程任务管理器"""
    
    def __init__(self):
        """初始化任务管理器"""
        # 存储运行中的任务: {task_key: {'thread': Thread, 'task_instance': Task, 'device_id': str, 'task_type': str}}
        self._tasks: Dict[str, dict] = {}
        self._lock = threading.Lock()  # 线程锁，确保线程安全
        
        # 任务类型映射
        self._task_classes = {
            'baotu': Baotu,
            'shimen': Shimen,
        }
    
    def _get_task_key(self, device_id: str, task_type: str) -> str:
        """生成任务唯一标识"""
        return f"{device_id}_{task_type}"
    
    def start_task(self, device_id: str, task_type: str) -> bool:
        """
        启动任务
        
        参数:
            device_id: 设备ID
            task_type: 任务类型 ('baotu' 或 'shimen')
        
        返回:
            bool: 是否成功启动
        """
        if task_type not in self._task_classes:
            print(f"未知的任务类型: {task_type}")
            return False
        
        task_key = self._get_task_key(device_id, task_type)
        
        with self._lock:
            # 检查任务是否已存在
            if task_key in self._tasks:
                task_info = self._tasks[task_key]
                if task_info['thread'].is_alive():
                    print(f"任务 {task_key} 已在运行中")
                    return False
                else:
                    # 清理已停止的任务
                    del self._tasks[task_key]
            
            # 创建任务实例
            try:
                task_class = self._task_classes[task_type]
                task_instance = task_class(device_id)
                
                # 创建线程运行任务
                thread = threading.Thread(
                    target=self._run_task,
                    args=(task_instance, device_id, task_type, task_key),
                    daemon=True,
                    name=f"Task-{task_key}"
                )
                
                # 保存任务信息
                self._tasks[task_key] = {
                    'thread': thread,
                    'task_instance': task_instance,
                    'device_id': device_id,
                    'task_type': task_type,
                    'start_time': time.time(),
                }
                
                # 启动线程
                thread.start()
                print(f"已启动任务: {task_key} (设备: {device_id}, 类型: {task_type})")
                return True
                
            except Exception as e:
                print(f"启动任务失败 {task_key}: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def _run_task(self, task_instance, device_id: str, task_type: str, task_key: str):
        """
        在独立线程中运行任务
        
        参数:
            task_instance: 任务实例
            device_id: 设备ID
            task_type: 任务类型
            task_key: 任务唯一标识
        """
        try:
            print(f"[{task_key}] 任务开始执行")
            # 调用任务的 start 方法
            if hasattr(task_instance, 'start'):
                task_instance.start()
            else:
                print(f"[{task_key}] 任务实例没有 start 方法")
        except Exception as e:
            print(f"[{task_key}] 任务执行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 任务结束后清理
            with self._lock:
                if task_key in self._tasks:
                    print(f"[{task_key}] 任务已结束")
                    # 注意：这里不删除任务信息，保留以便查询状态
                    # 如果需要立即删除，可以取消注释下面这行
                    # del self._tasks[task_key]
    
    def stop_task(self, device_id: str, task_type: Optional[str] = None) -> bool:
        """
        停止任务
        
        参数:
            device_id: 设备ID
            task_type: 任务类型，如果为 None 则停止该设备的所有任务
        
        返回:
            bool: 是否成功停止
        """
        with self._lock:
            if task_type:
                # 停止指定类型的任务
                task_key = self._get_task_key(device_id, task_type)
                if task_key in self._tasks:
                    return self._stop_single_task(task_key)
                else:
                    print(f"任务 {task_key} 不存在")
                    return False
            else:
                # 停止该设备的所有任务
                stopped_count = 0
                task_keys_to_stop = [
                    key for key, info in self._tasks.items()
                    if info['device_id'] == device_id
                ]
                
                for task_key in task_keys_to_stop:
                    if self._stop_single_task(task_key):
                        stopped_count += 1
                
                if stopped_count > 0:
                    print(f"已停止设备 {device_id} 的 {stopped_count} 个任务")
                    return True
                else:
                    print(f"设备 {device_id} 没有运行中的任务")
                    return False
    
    def _stop_single_task(self, task_key: str) -> bool:
        """停止单个任务"""
        if task_key not in self._tasks:
            return False
        
        task_info = self._tasks[task_key]
        thread = task_info['thread']
        task_instance = task_info['task_instance']
        
        if not thread.is_alive():
            print(f"任务 {task_key} 已经停止")
            del self._tasks[task_key]
            return True
        
        # 尝试调用任务的 stop 方法
        try:
            if hasattr(task_instance, 'stop'):
                task_instance.stop()
        except Exception as e:
            print(f"调用任务 stop 方法失败 {task_key}: {e}")
        
        # 等待线程结束（最多等待5秒）
        thread.join(timeout=5.0)
        
        if thread.is_alive():
            print(f"警告: 任务 {task_key} 的线程在5秒后仍未结束")
            return False
        else:
            print(f"任务 {task_key} 已停止")
            del self._tasks[task_key]
            return True
    
    def get_task_status(self, device_id: Optional[str] = None) -> Dict:
        """
        获取任务状态
        
        参数:
            device_id: 设备ID，如果为 None 则返回所有任务状态
        
        返回:
            dict: 任务状态信息
        """
        with self._lock:
            if device_id:
                # 返回指定设备的任务状态
                tasks = {
                    key: info for key, info in self._tasks.items()
                    if info['device_id'] == device_id
                }
            else:
                # 返回所有任务状态
                tasks = self._tasks.copy()
            
            status = {}
            for task_key, task_info in tasks.items():
                thread = task_info['thread']
                status[task_key] = {
                    'device_id': task_info['device_id'],
                    'task_type': task_info['task_type'],
                    'is_running': thread.is_alive(),
                    'start_time': task_info.get('start_time', 0),
                    'runtime': time.time() - task_info.get('start_time', time.time()) if thread.is_alive() else 0,
                }
            
            return status
    
    def get_all_running_tasks(self) -> list:
        """获取所有运行中的任务列表"""
        with self._lock:
            return [
                {
                    'task_key': key,
                    'device_id': info['device_id'],
                    'task_type': info['task_type'],
                }
                for key, info in self._tasks.items()
                if info['thread'].is_alive()
            ]


# 全局任务管理器实例
_task_manager = None


def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例（单例模式）"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

