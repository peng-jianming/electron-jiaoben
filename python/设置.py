"""
全局设置
"""
import os

# 项目根目录（与 main.py 同目录）
项目根目录 = os.path.dirname(os.path.abspath(__file__))

# 资源目录
资源目录 = os.path.join(项目根目录, "资源")

# 缓存目录
缓存目录 = os.path.join(资源目录, "截图缓存目录")

# 未知界面截图目录
未知截图目录 = os.path.join(资源目录, "未知界面截图目录")

任务目录 = os.path.join(项目根目录, "任务")

# 日志目录
日志目录 = os.path.join(资源目录, "日志")

# 字库文件路径
字库文件路径 = os.path.join(资源目录, "字库.json")

# 账号文件路径
账号文件路径 = os.path.join(资源目录, "账号.json")

# 界面配置文件路径
界面配置文件路径 = os.path.join(资源目录, "界面配置.json")

# YOLO 模型路径
模型文件路径 = os.path.join(资源目录, "模型.pt")

# 提示音乐路径
音乐文件路径 = os.path.join(资源目录, "提示音乐.mp3")

# ADB 路径（优先使用项目内置 ADB）
# 默认内置目录：<项目根目录>/adb/adb.exe
内置ADB路径 = os.path.join(项目根目录, "adb", "adb.exe")
默认系统ADB路径 = r"C:\platform-tools\adb.exe"

# 允许通过环境变量 ADB_PATH 覆盖
环境ADB路径 = os.environ.get("ADB_PATH")

if 环境ADB路径 and os.path.exists(环境ADB路径):
    ADB路径 = 环境ADB路径
elif os.path.exists(内置ADB路径):
    ADB路径 = 内置ADB路径
elif os.path.exists(默认系统ADB路径):
    ADB路径 = 默认系统ADB路径
else:
    # 最后退回到系统 PATH 中的 adb 命令名
    ADB路径 = "adb"

# Socket.IO 服务器地址
服务器地址 = "http://127.0.0.1:7072"


# 确保目录存在
os.makedirs(缓存目录, exist_ok=True)
os.makedirs(未知截图目录, exist_ok=True)
