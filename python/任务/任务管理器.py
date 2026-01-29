"""
任务管理器 - 多线程任务管理

任务类型由 任务发现 自动发现，新增任务只需在 任务 文件夹新建模块并定义 任务类型名、创建任务，无需在此处引入。
"""
import threading
import time
from .任务发现 import 发现所有任务


class 任务管理器类:
    """多线程任务管理器"""

    def __init__(self):
        """初始化任务管理器"""
        self._任务集合 = {}
        self._任务队列集合 = {}
        self._当前队列索引 = {}
        self._锁 = threading.Lock()

        # 任务类型映射（由任务发现自动收集）
        self._任务类型映射 = 发现所有任务()

    def _获取任务键(self, 设备ID, 任务类型):
        """生成任务唯一标识"""
        return f"{设备ID}_{任务类型}"

    def _清理队列(self, 设备ID):
        """清理任务队列信息"""
        if 设备ID in self._任务队列集合:
            del self._任务队列集合[设备ID]
        if 设备ID in self._当前队列索引:
            del self._当前队列索引[设备ID]

    def _启动任务(self, 设备ID, 任务类型):
        """内部方法：启动任务"""
        if 任务类型 not in self._任务类型映射:
            print(f"未知的任务类型: {任务类型}")
            return False

        任务键 = self._获取任务键(设备ID, 任务类型)
        with self._锁:
            if 任务键 in self._任务集合:
                if self._任务集合[任务键]['线程'].is_alive():
                    print(f"任务 {任务键} 已在运行中")
                    return False
                del self._任务集合[任务键]

            try:
                任务实例 = self._任务类型映射[任务类型](设备ID)
                线程 = threading.Thread(
                    target=self._运行任务,
                    args=(任务实例, 设备ID, 任务类型, 任务键),
                    daemon=True,
                    name=f"Task-{任务键}"
                )
                self._任务集合[任务键] = {
                    '线程': 线程,
                    '任务实例': 任务实例,
                    '设备ID': 设备ID,
                    '任务类型': 任务类型,
                    '开始时间': time.time(),
                }
                线程.start()
                print(f"已启动任务: {任务键}")
                return True
            except Exception as e:
                print(f"启动任务失败 {任务键}: {e}")
                import traceback
                traceback.print_exc()
                return False

    def 启动任务队列(self, 设备ID, 任务队列):
        """
        启动任务队列

        参数:
            设备ID: 设备ID
            任务队列: 任务类型列表，例如 ['师门任务', '宝图任务']

        返回:
            bool: 是否成功启动
        """
        if not isinstance(任务队列, list) or not 任务队列:
            print(f"无效的任务队列: {任务队列}")
            return False

        无效类型 = [t for t in 任务队列 if t not in self._任务类型映射]
        if 无效类型:
            print(f"未知的任务类型: {无效类型}")
            return False

        with self._锁:
            if 设备ID in self._任务队列集合:
                print(f"设备 {设备ID} 已有任务队列在运行")
                return False
            self._任务队列集合[设备ID] = 任务队列.copy()
            self._当前队列索引[设备ID] = 0

        return self._启动任务(设备ID, 任务队列[0])

    def _运行任务(self, 任务实例, 设备ID, 任务类型, 任务键):
        """在独立线程中运行任务"""
        try:
            print(f"[{任务键}] 任务开始执行")
            if hasattr(任务实例, '开始'):
                任务实例.开始()
            else:
                print(f"[{任务键}] 任务实例没有 开始 方法")
        except Exception as e:
            print(f"[{任务键}] 任务执行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            with self._锁:
                if 任务键 in self._任务集合:
                    print(f"[{任务键}] 任务已结束")
                有队列 = 设备ID in self._任务队列集合

            if 有队列:
                self._启动下一个任务(设备ID)

    def 停止任务(self, 设备ID):
        """停止任务队列"""
        with self._锁:
            if 设备ID not in self._任务队列集合:
                print(f"设备 {设备ID} 没有运行中的任务队列")
                return False

            print(f"[{设备ID}] 停止任务队列")
            self._清理队列(设备ID)

            要停止的任务键列表 = [
                键 for 键, 信息 in self._任务集合.items()
                if 信息['设备ID'] == 设备ID
            ]

        停止数量 = 0
        for 任务键 in 要停止的任务键列表:
            if self._停止单个任务(任务键):
                停止数量 += 1

        if 停止数量 > 0:
            print(f"已停止设备 {设备ID} 的 {停止数量} 个任务")
            return True
        print(f"设备 {设备ID} 没有运行中的任务")
        return False

    def _启动下一个任务(self, 设备ID):
        """启动任务队列中的下一个任务"""
        with self._锁:
            if 设备ID not in self._任务队列集合:
                return

            队列 = self._任务队列集合[设备ID]
            当前索引 = self._当前队列索引.get(设备ID, 0)
            当前索引 += 1

            if 当前索引 < len(队列):
                self._当前队列索引[设备ID] = 当前索引
                下一个任务类型 = 队列[当前索引]
                print(f"[{设备ID}] 任务队列: 启动下一个任务 ({当前索引 + 1}/{len(队列)}): {下一个任务类型}")
                threading.Timer(0.5, lambda: self._启动任务(设备ID, 下一个任务类型)).start()
            else:
                print(f"[{设备ID}] 任务队列执行完毕，共完成 {len(队列)} 个任务")
                self._清理队列(设备ID)

    def _停止单个任务(self, 任务键):
        """停止单个任务"""
        if 任务键 not in self._任务集合:
            return False

        任务信息 = self._任务集合[任务键]
        线程 = 任务信息['线程']
        任务实例 = 任务信息['任务实例']

        if not 线程.is_alive():
            print(f"任务 {任务键} 已经停止")
            del self._任务集合[任务键]
            return True

        try:
            if hasattr(任务实例, '停止'):
                任务实例.停止()
        except Exception as e:
            print(f"调用任务停止方法失败 {任务键}: {e}")

        线程.join(timeout=5.0)

        if 线程.is_alive():
            print(f"警告: 任务 {任务键} 的线程在5秒后仍未结束")
            return False
        else:
            print(f"任务 {任务键} 已停止")
            del self._任务集合[任务键]
            return True

    def 获取任务状态(self, 设备ID=None):
        """获取任务状态"""
        with self._锁:
            任务集合 = {
                键: 信息 for 键, 信息 in self._任务集合.items()
                if not 设备ID or 信息['设备ID'] == 设备ID
            }

            状态 = {}
            for 任务键, 任务信息 in 任务集合.items():
                线程 = 任务信息['线程']
                开始时间 = 任务信息.get('开始时间', time.time())
                状态[任务键] = {
                    '设备ID': 任务信息['设备ID'],
                    '任务类型': 任务信息['任务类型'],
                    '运行中': 线程.is_alive(),
                    '开始时间': 开始时间,
                    '运行时长': time.time() - 开始时间 if 线程.is_alive() else 0,
                }

            设备列表 = [设备ID] if 设备ID else list(self._任务队列集合.keys())
            for 设备 in 设备列表:
                if 设备 in self._任务队列集合:
                    队列信息 = {
                        '队列': self._任务队列集合[设备],
                        '当前索引': self._当前队列索引.get(设备, 0),
                        '总数': len(self._任务队列集合[设备]),
                    }
                    if 设备ID:
                        状态['_队列'] = 队列信息
                    else:
                        if 设备 not in 状态:
                            状态[设备] = {}
                        状态[设备]['_队列'] = 队列信息

            return 状态

    def 获取所有运行中的任务(self):
        """获取所有运行中的任务列表"""
        with self._锁:
            return [
                {
                    '任务键': 键,
                    '设备ID': 信息['设备ID'],
                    '任务类型': 信息['任务类型'],
                }
                for 键, 信息 in self._任务集合.items()
                if 信息['线程'].is_alive()
            ]


# 全局任务管理器实例
_任务管理器 = None


def 获取任务管理器():
    """获取全局任务管理器实例（单例模式）"""
    global _任务管理器
    if _任务管理器 is None:
        _任务管理器 = 任务管理器类()
    return _任务管理器
