import os
import re
import time
from datetime import datetime
import threading

# Windows 文件名非法字符：< > : " / \ | ? * 及控制字符
_非法文件名字符 = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _账号到日志文件名片段(账号: str) -> str:
    s = _非法文件名字符.sub("_", str(账号))
    return s.strip() or "unknown"


class 日志管理器类:
    def __init__(self, 日志目录, 日志保留时间=2):
        self.日志目录 = 日志目录
        self.清理线程标志位 = True
        # 注册/初始化时先清理一次过期日志
        self.清理日志存档(日志保留时间)

    def __del__(self):
        self.清理线程标志位 = False

    def 清理日志存档(self, 日志保留时间):
        """删除日志目录下超过保留天数的日志文件。"""
        # 保底：确保目录存在
        os.makedirs(self.日志目录, exist_ok=True)

        try:
            日志保留时间 = float(日志保留时间)
        except (TypeError, ValueError):
            日志保留时间 = 0

        # 保留时间 <= 0：视为不清理
        if 日志保留时间 <= 0:
            return

        cutoff_ts = time.time() - 日志保留时间 * 24 * 60 * 60

        try:
            entries = os.listdir(self.日志目录)
        except OSError:
            return

        for name in entries:
            # 当前项目写入日志都是 .txt；只清理文本日志避免误删其他文件
            if not name.lower().endswith(".txt"):
                continue

            file_path = os.path.join(self.日志目录, name)
            if not os.path.isfile(file_path):
                continue

            try:
                mtime = os.path.getmtime(file_path)
            except OSError:
                continue

            if mtime < cutoff_ts:
                try:
                    os.remove(file_path)
                except OSError:
                    # 删除失败不影响主流程
                    pass

    def 定期清理日志存档(self, 日志保留时间, 间隔秒=3600):
        """定期清理过期日志（当前未在 __init__ 中自动启动线程）。"""
        while self.清理线程标志位:
            self.清理日志存档(日志保留时间)
            time.sleep(间隔秒)

    def 写入日志(self, 账号, 内容):
        now = datetime.now()
        当前日期 = now.strftime("%Y-%m-%d")
        安全账号 = _账号到日志文件名片段(账号)
        日志路径 = os.path.join(self.日志目录, f"{安全账号}_{当前日期}.txt")
        with open(日志路径, "a", encoding="utf-8") as f:
            当前时间 = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            内容 = f"{当前时间} {内容}\n"
            f.write(内容)

    def 打开日志(self, 账号):
        now = datetime.now()
        当前日期 = now.strftime("%Y-%m-%d")
        安全账号 = _账号到日志文件名片段(账号)
        日志路径 = os.path.join(self.日志目录, f"{安全账号}_{当前日期}.txt")
        if os.path.exists(日志路径):
            cmd = f"start {日志路径}"
            os.system(cmd)
            return True
        else:  # 创建目录
            with open(日志路径, "w", encoding="utf-8") as file:
                pass
            cmd = f"start {日志路径}"
            os.system(cmd)
