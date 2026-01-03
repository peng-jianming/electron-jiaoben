import threading
import time
from baotu import create_baotu_task
from zhuagui import create_zhuagui_task
from shimen import create_shimen_task

class TaskManager:
    """多线程任务管理器"""
    
    def __init__(self):
        """初始化任务管理器"""
        # 存储运行中的任务: {task_key: {'thread': Thread, 'task_instance': Task, 'device_id': str, 'task_type': str}}
        self._tasks = {}
        # 存储任务队列: {device_id: [task_type1, task_type2, ...]}
        self._task_queues = {}
        # 存储当前执行的任务在队列中的索引: {device_id: index}
        self._current_queue_index = {}
        self._lock = threading.Lock()  # 线程锁，确保线程安全
        
        # 任务类型映射（工厂函数或类，接收 device_id 参数）
        self._task_classes = {
            'baotu': create_baotu_task,
            'zhuagui': create_zhuagui_task,
            'shimen': create_shimen_task
        }
    
    def _get_task_key(self, device_id, task_type):
        """生成任务唯一标识"""
        return f"{device_id}_{task_type}"
    
    def _cleanup_queue(self, device_id):
        """清理任务队列信息"""
        if device_id in self._task_queues:
            del self._task_queues[device_id]
        if device_id in self._current_queue_index:
            del self._current_queue_index[device_id]
    
    def _start_task(self, device_id, task_type):
        """
        内部方法：启动任务（用于任务队列）
        
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
                if self._tasks[task_key]['thread'].is_alive():
                    print(f"任务 {task_key} 已在运行中")
                    return False
                del self._tasks[task_key]
            
            # 创建任务实例
            try:
                task_instance = self._task_classes[task_type](device_id)
                thread = threading.Thread(
                    target=self._run_task,
                    args=(task_instance, device_id, task_type, task_key),
                    daemon=True,
                    name=f"Task-{task_key}"
                )
                self._tasks[task_key] = {
                    'thread': thread,
                    'task_instance': task_instance,
                    'device_id': device_id,
                    'task_type': task_type,
                    'start_time': time.time(),
                }
                thread.start()
                print(f"已启动任务: {task_key} (设备: {device_id}, 类型: {task_type})")
                return True
            except Exception as e:
                print(f"启动任务失败 {task_key}: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def start_task_queue(self, device_id, task_queue):
        """
        启动任务队列（按顺序执行多个任务）
        
        参数:
            device_id: 设备ID
            task_queue: 任务类型列表，例如 ['shimen', 'baotu']
        
        返回:
            bool: 是否成功启动
        """
        if not isinstance(task_queue, list) or not task_queue:
            print(f"无效的任务队列: {task_queue}")
            return False
        
        # 验证所有任务类型
        invalid_types = [t for t in task_queue if t not in self._task_classes]
        if invalid_types:
            print(f"未知的任务类型: {invalid_types}")
            return False
        
        with self._lock:
            if device_id in self._task_queues:
                print(f"设备 {device_id} 已有任务队列在运行")
                return False
            self._task_queues[device_id] = task_queue.copy()
            self._current_queue_index[device_id] = 0
        
        return self._start_task(device_id, task_queue[0])
    
    def _run_task(self, task_instance, device_id, task_type, task_key):
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
            with self._lock:
                if task_key in self._tasks:
                    print(f"[{task_key}] 任务已结束")
                has_queue = device_id in self._task_queues
            
            if has_queue:
                self._start_next_task_in_queue(device_id)
    
    def stop_task(self, device_id):
        """
        停止任务队列（停止该设备的所有任务）
        
        参数:
            device_id: 设备ID
        
        返回:
            bool: 是否成功停止
        """
        with self._lock:
            # 只能停止任务队列，不能停止单个任务
            if device_id not in self._task_queues:
                print(f"设备 {device_id} 没有运行中的任务队列")
                return False
            
            print(f"[{device_id}] 停止任务队列")
            # 清理任务队列信息，防止启动下一个任务
            self._cleanup_queue(device_id)
            
            # 获取该设备的所有任务
            task_keys_to_stop = [
                key for key, info in self._tasks.items()
                if info['device_id'] == device_id
            ]
        
        # 停止该设备的所有任务
        stopped_count = 0
        for task_key in task_keys_to_stop:
            if self._stop_single_task(task_key):
                stopped_count += 1
        
        if stopped_count > 0:
            print(f"已停止设备 {device_id} 的 {stopped_count} 个任务")
            return True
        print(f"设备 {device_id} 没有运行中的任务")
        return False
    
    def _start_next_task_in_queue(self, device_id):
        """启动任务队列中的下一个任务（必须在锁外调用）"""
        with self._lock:
            if device_id not in self._task_queues:
                return
            
            queue = self._task_queues[device_id]
            current_index = self._current_queue_index.get(device_id, 0)
            
            # 移动到下一个任务
            current_index += 1
            
            if current_index < len(queue):
                self._current_queue_index[device_id] = current_index
                next_task_type = queue[current_index]
                print(f"[{device_id}] 任务队列: 启动下一个任务 ({current_index + 1}/{len(queue)}): {next_task_type}")
                threading.Timer(0.5, lambda: self._start_task(device_id, next_task_type)).start()
            else:
                print(f"[{device_id}] 任务队列执行完毕，共完成 {len(queue)} 个任务")
                self._cleanup_queue(device_id)
    
    def _stop_single_task(self, task_key):
        """停止单个任务（内部方法，仅用于停止任务队列中的任务）"""
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
    
    def get_task_status(self, device_id=None):
        """
        获取任务状态
        
        参数:
            device_id: 设备ID，如果为 None 则返回所有任务状态
        
        返回:
            dict: 任务状态信息
        """
        with self._lock:
            tasks = {
                key: info for key, info in self._tasks.items()
                if not device_id or info['device_id'] == device_id
            }
            
            status = {}
            for task_key, task_info in tasks.items():
                thread = task_info['thread']
                start_time = task_info.get('start_time', time.time())
                status[task_key] = {
                    'device_id': task_info['device_id'],
                    'task_type': task_info['task_type'],
                    'is_running': thread.is_alive(),
                    'start_time': start_time,
                    'runtime': time.time() - start_time if thread.is_alive() else 0,
                }
            
            # 添加任务队列信息
            devices = [device_id] if device_id else list(self._task_queues.keys())
            for dev_id in devices:
                if dev_id in self._task_queues:
                    queue_info = {
                        'queue': self._task_queues[dev_id],
                        'current_index': self._current_queue_index.get(dev_id, 0),
                        'total': len(self._task_queues[dev_id]),
                    }
                    if device_id:
                        status['_queue'] = queue_info
                    else:
                        if dev_id not in status:
                            status[dev_id] = {}
                        status[dev_id]['_queue'] = queue_info
            
            return status
    
    def get_all_running_tasks(self):
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


def get_task_manager():
    """获取全局任务管理器实例（单例模式）"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

