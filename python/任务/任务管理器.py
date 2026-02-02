"""
任务管理器 - 多线程任务管理

"""
import threading
import time

from 核心.设备控制器 import 设备控制器类


class 任务管理器类:
    """多线程任务管理器"""

    def __init__(self):
        """初始化任务管理器"""
        self._任务集合 = {}
        self._任务队列集合 = {}
        self._当前队列索引 = {}
        self._锁 = threading.Lock()

        # 任务类型映射（由任务发现自动收集）
        self._任务类型映射 = 发现所有任务模块()

    def _获取任务键(self, 设备ID, 任务类型):
        """生成任务唯一标识"""
        return f"{设备ID}_{任务类型}"

    def _清理队列(self, 设备ID):
        """清理任务队列信息"""
        if 设备ID in self._任务队列集合:
            del self._任务队列集合[设备ID]
        if 设备ID in self._当前队列索引:
            del self._当前队列索引[设备ID]

    def _发送任务状态更新(self, 设备ID, 清空=False):
        """发送任务状态更新到前端"""
        try:
            控制器 = 设备控制器类(设备ID)
            if 清空:
                控制器.更新设备状态(当前任务="", 下一任务="")
            else:
                """获取队列中的当前任务和下一任务"""
                if 设备ID not in self._任务队列集合:
                    return None, None
                
                队列 = self._任务队列集合[设备ID]
                索引 = self._当前队列索引.get(设备ID, 0)
                
                当前任务 = 队列[索引] if 索引 < len(队列) else None
                下一任务 = 队列[索引 + 1] if 索引 + 1 < len(队列) else None
                控制器.更新设备状态(当前任务=当前任务 or "", 下一任务=下一任务 or "")
        except Exception as e:
            print(f"发送任务状态更新失败: {e}")


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
                
                # 发送任务状态更新到前端
                self._发送任务状态更新(设备ID, 清空=False)
                
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

    def 结束任务(self, 设备ID):
        """结束任务队列"""
        with self._锁:
            # 检查是否有任务队列或运行中的任务
            有队列 = 设备ID in self._任务队列集合
            要结束的任务键列表 = [
                键 for 键, 信息 in self._任务集合.items()
                if 信息['设备ID'] == 设备ID
            ]
            
            if not 有队列 and not 要结束的任务键列表:
                print(f"设备 {设备ID} 没有运行中的任务")
                return False

            print(f"[{设备ID}] 结束任务队列")
            # 先清理队列，防止任务结束后触发下一个任务
            self._清理队列(设备ID)

        # 在锁外结束任务（因为结束可能需要等待线程结束）
        结束数量 = 0
        for 任务键 in 要结束的任务键列表:
            if self._结束单个任务(任务键):
                结束数量 += 1

        # 发送清空状态到前端（包括清除暂停状态）
        self._发送任务状态更新(设备ID, 清空=True)
        self._发送暂停状态更新(设备ID, 已暂停=False)

        if 结束数量 > 0:
            print(f"已结束设备 {设备ID} 的 {结束数量} 个任务")
            return True
        return True  # 即使没有任务要结束，队列已清理也算成功

    def 暂停任务(self, 设备ID):
        """暂停设备的当前任务"""
        with self._锁:
            # 查找该设备正在运行的任务
            for 任务键, 任务信息 in self._任务集合.items():
                if 任务信息['设备ID'] == 设备ID and 任务信息['线程'].is_alive():
                    任务实例 = 任务信息['任务实例']
                    if hasattr(任务实例, '暂停'):
                        任务实例.暂停()
                        print(f"[{设备ID}] 任务已暂停")
                        # 发送暂停状态到前端
                        self._发送暂停状态更新(设备ID, 已暂停=True)
                        return True

        print(f"设备 {设备ID} 没有可暂停的任务")
        return False

    def 恢复任务(self, 设备ID):
        """恢复设备的当前任务"""
        with self._锁:
            # 查找该设备正在运行的任务
            for 任务键, 任务信息 in self._任务集合.items():
                if 任务信息['设备ID'] == 设备ID and 任务信息['线程'].is_alive():
                    任务实例 = 任务信息['任务实例']
                    if hasattr(任务实例, '恢复'):
                        任务实例.恢复()
                        print(f"[{设备ID}] 任务已恢复")
                        # 发送恢复状态到前端
                        self._发送暂停状态更新(设备ID, 已暂停=False)
                        return True

        print(f"设备 {设备ID} 没有可恢复的任务")
        return False

    def _发送暂停状态更新(self, 设备ID, 已暂停):
        """发送暂停状态更新到前端"""
        try:
            控制器 = 设备控制器类(设备ID)
            控制器.更新设备状态(已暂停=已暂停)
        except Exception as e:
            print(f"发送暂停状态更新失败: {e}")

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
                # 任务队列完成，发送清空状态
                self._发送任务状态更新(设备ID, 清空=True)

    def _结束单个任务(self, 任务键):
        """结束单个任务"""
        if 任务键 not in self._任务集合:
            return False

        任务信息 = self._任务集合[任务键]
        线程 = 任务信息['线程']
        任务实例 = 任务信息['任务实例']

        if not 线程.is_alive():
            print(f"任务 {任务键} 已经结束")
            del self._任务集合[任务键]
            return True

        try:
            # 调用结束方法（会设置 _运行中=False 并唤醒暂停等待）
            if hasattr(任务实例, '结束'):
                任务实例.结束()
        except Exception as e:
            print(f"调用任务结束方法失败 {任务键}: {e}")

        线程.join(timeout=5.0)

        if 线程.is_alive():
            print(f"警告: 任务 {任务键} 的线程在5秒后仍未结束")
            return False
        else:
            print(f"任务 {任务键} 已结束")
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





def 发现所有任务模块():
    import pkgutil
    import importlib
    import sys
    """
    扫描 任务 包下所有模块，以文件名作为任务名，收集 文件下的 创建任务 函数。

    返回:
        dict: { 任务名: 创建任务函数 }
    """
    任务包 = sys.modules[__name__].__package__
    任务包模块 = sys.modules.get(任务包)
    if 任务包模块 is None:
        return {}

    结果 = {}
    忽略模块名 = {'任务管理器', '__init__'}

    for 查找器, 模块全名, 是否包 in pkgutil.iter_modules(任务包模块.__path__, 任务包 + '.'):
        # 文件名（不含 .py）即任务名
        任务名 = 模块全名.split('.')[-1]
        if 任务名 in 忽略模块名:
            continue
        try:
            模块 = importlib.import_module(模块全名)
        except Exception as e:
            print(f"[任务发现] 导入模块 {模块全名} 失败: {e}")
            continue

        创建任务 = getattr(模块, '创建任务', None)

        if 创建任务 is None:
            print(f"[任务发现] 跳过 {任务名}: 缺少 创建任务")
            continue
        if not callable(创建任务):
            print(f"[任务发现] 跳过 {任务名}: 创建任务 不可调用")
            continue

        结果[任务名] = 创建任务
        print(f"[任务发现] 已注册任务: {任务名}")

    return 结果
