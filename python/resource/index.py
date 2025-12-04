import os
import importlib

# 获取当前目录下的所有文件夹（排除 cache 和 __pycache__）
resource_dir = os.path.dirname(__file__)
folders = [
    name for name in os.listdir(resource_dir)
    if os.path.isdir(os.path.join(resource_dir, name)) 
    and name not in ('cache', '__pycache__')
]

# 动态导入所有子文件夹的 index.py 并收集导出内容
__all__ = []
ms = {}  # 用于通过 ms['key'] 方式访问

for folder_name in folders:
    folder_index_path = os.path.join(resource_dir, folder_name, 'index.py')
    if os.path.exists(folder_index_path):
        # 动态导入子模块
        module = importlib.import_module(f'.{folder_name}.index', package=__package__)
        
        # 获取模块的 __all__ 或所有公开属性
        if hasattr(module, '__all__'):
            export_names = module.__all__
        else:
            export_names = [name for name in dir(module) if not name.startswith('_')]
        
        # 将导出的内容添加到当前模块的全局命名空间和 ms 字典
        for name in export_names:
            value = getattr(module, name)
            globals()[name] = value
            ms[name] = value
            __all__.append(name)

__all__.append('ms')
