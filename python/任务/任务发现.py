"""
任务发现 - 自动发现 任务 包下的所有任务，无需在任务管理器中手动引入

约定：每个任务模块需定义：
  - 任务类型名: str   # 用于任务队列的 key，与前端约定一致，如 "宝图任务"
  - 创建任务: callable(设备ID)  # 工厂函数，接收设备ID，返回任务执行器实例

新增任务时：在 任务 文件夹新建 xxx.py，定义上述两个变量即可，无需改任务管理器。
"""
import pkgutil
import importlib
import sys


def 发现所有任务():
    """
    扫描 任务 包下所有模块，收集符合约定的任务类型名与创建函数。

    返回:
        dict: { 任务类型名: 创建任务函数 }
    """
    任务包 = sys.modules[__name__].__package__
    任务包模块 = sys.modules.get(任务包)
    if 任务包模块 is None:
        return {}

    结果 = {}
    忽略模块名 = {'任务管理器', '__init__', '任务发现'}

    for 查找器, 模块名, 是否包 in pkgutil.iter_modules(任务包模块.__path__, 任务包 + '.'):
        if 模块名.split('.')[-1] in 忽略模块名:
            continue
        try:
            模块 = importlib.import_module(模块名)
        except Exception as e:
            print(f"[任务发现] 导入模块 {模块名} 失败: {e}")
            continue

        任务类型名 = getattr(模块, '任务类型名', None)
        创建任务 = getattr(模块, '创建任务', None)

        if 任务类型名 is None or 创建任务 is None:
            print(f"[任务发现] 跳过 {模块名}: 缺少 任务类型名 或 创建任务")
            continue
        if not callable(创建任务):
            print(f"[任务发现] 跳过 {模块名}: 创建任务 不可调用")
            continue

        结果[任务类型名] = 创建任务
        print(f"[任务发现] 已注册任务: {任务类型名}")

    return 结果
