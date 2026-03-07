import os
import time
from datetime import datetime
import threading

class 日志管理器类:
    def __init__(self, 日志目录, 日志保留时间=1):
        self.日志目录 = 日志目录
        self.清理线程标志位 = True
        self.定期清理日志存档(日志保留时间)

    def __del__(self):
        self.清理线程标志位 = False
        

    def 定期清理日志存档(self, 日志保留时间):
        def _定期清理日志缓存():
            s = time.time()
            while self.清理线程标志位:
                time.sleep(0.1)  # 间隔
                if time.time() - s < 60:
                    continue
                else:
                    s = time.time()
                for file in os.listdir(self.日志目录):
                    if ".txt" in file:
                        # 将字符串转换为datetime对象
                        try:
                            日志日期 = file.split(".txt")[0].split("_")[1]
                            target_date = datetime.strptime(日志日期, "%Y-%m-%d")
                            current_date = datetime.now()  # 获取当前日期和时间（如果需要仅日期部分，可以使用.date()方法）
                            delta = target_date - current_date  # 计算两个日期之间的时间差
                            days_difference = delta.days  # 获取相差的天数
                            if days_difference > 日志保留时间:  # 如果delta.days是负数，说明当前日期在目标日期之后
                                os.remove(os.path.join(self.日志目录, file))
                            else:
                                pass
                        except Exception as e:
                            print("日期文件名称格式不符合 %s" % e)

        threading.Thread(target=_定期清理日志缓存, daemon=True).start()

    def 写入日志(self, 账号, 内容):
        now = datetime.now()
        当前日期 = now.strftime("%Y-%m-%d")
        日志路径 = f"{self.日志目录}/{账号}_{当前日期}.txt"
        with open(日志路径, "a", encoding="utf-8") as f:
            当前时间 = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            内容 = f"{当前时间} {内容}\n"
            f.write(内容)


    def 打开日志(self, 账号):
        now = datetime.now()
        当前日期 = now.strftime("%Y-%m-%d")
        日志路径 = f"{self.日志目录}/{账号}_{当前日期}.txt"
        if os.path.exists(日志路径):
            cmd = f"start {日志路径}"
            os.system(cmd)
            return True
        else:  # 创建目录
            with open(日志路径, 'w', encoding="utf-8") as file:
                pass
            cmd = f"start {日志路径}"
            os.system(cmd)
