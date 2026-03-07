"""
群控图色脚本 Python 后端入口
通过 Socket.IO 与 Electron 前端通信
以账号为主体，动态从设备池中分配空闲设备运行任务。
"""

import json
import os
import socketio
import threading
from queue import Queue
from 设置 import 服务器地址, 最大线程数, 资源目录, 账号文件路径, 日志目录
from core.线程控制器 import 线程控制器类
from core.ADB控制器 import ADB控制器类
from core.任务管理器 import 任务管理器类, 发现所有任务模块
from core.日志管理器 import 日志管理器类

class 主程序:
    def __init__(self):
        self._客户端 = None
        self.消息队列 = Queue()
        self.日志管理器 = 日志管理器类(日志目录)
        self.设备列表 = []           # [{"设备ID": str, "状态": "空闲"|"占用", "占用账号": str}]
        self.等待队列 = []           # [(账号key, 数据dict)]
        self._池锁 = threading.Lock()

        self.初始化客户端()

    # ─── Socket 初始化 ─────────────────────────

    def 初始化客户端(self):
        if self._客户端 is None:
            self._客户端 = socketio.Client()

            @self._客户端.on("message")
            def 收到消息(数据):
                print(f"收到来自 Electron 的消息: {数据}")
                if isinstance(数据, dict) and 数据.get("类型"):
                    self.消息队列.put((数据.get("类型"), 数据))
                else:
                    print("忽略无效消息: 需为 dict 且包含 类型")

            @self._客户端.on("connect")
            def 连接成功():
                self.发送到Electron("backend-ready", True)

        if not any(t.name == "socket-worker" for t in threading.enumerate()):
            worker = threading.Thread(target=self.客户端消息队列处理, name="socket-worker")
            worker.start()

        if not self._客户端.connected:
            try:
                self._客户端.connect(服务器地址)
                print(f"Socket.IO 客户端已连接到: {服务器地址}")
            except Exception as e:
                print(f"Socket.IO 连接失败: {e}")

    def 客户端消息队列处理(self):
        self.线程控制器 = 线程控制器类(
            最大线程数量=最大线程数,
            回调函数=任务管理器类,
            线程结束后回调函数=self.线程结束回调,
            打印回调函数=self.更新账号数据,
        )
        while True:
            try:
                类型, 数据 = self.消息队列.get()
                处理器 = {
                    "打开日志": lambda d: self.日志管理器.打开日志(d.get("账号")),
                    "获取设备列表": lambda d: self.获取设备列表(),
                    "获取任务列表": lambda d: self.获取任务列表(),
                    "获取账号列表": lambda d: self.发送账号列表(),
                    "禁用设备": self.禁用设备,
                    "启用设备": self.启用设备,
                    "账号开始任务": self.账号开始任务,
                    "账号结束任务": self.账号结束任务,
                    "账号暂停任务": self.账号暂停任务,
                    "账号恢复任务": self.账号恢复任务,
                    "全部开始": self.全部开始,
                    "全部结束": lambda d: self.全部结束(),
                    "全部暂停": lambda d: self.全部暂停(),
                    "全部恢复": lambda d: self.全部恢复(),
                }
                if 类型 in 处理器:
                    处理器[类型](数据)
                else:
                    print(f"未知消息类型: {类型}")
            except Exception as e:
                import traceback
                print(f"Worker 处理消息异常: {e}")
                traceback.print_exc()
            finally:
                self.消息队列.task_done()

    def 发送到Electron(self, 前端接收事件名, 数据):
        try:
            data = {
                "cmd": "controller/example/从后端接收数据",
                "args": {"事件名": 前端接收事件名, "数据": 数据},
            }
            self._客户端.emit("socket-channel", data)
        except Exception as e:
            print(f"发送数据错误: {e}")

    # ─── 设备管理 ──────────────────────────────

    def 获取设备列表(self):
        adb = ADB控制器类()
        新设备IDs = adb.获取设备列表()
        已有映射 = {d["设备ID"]: d for d in self.设备列表}
        self.设备列表 = [
            已有映射.get(id, {"设备ID": id, "状态": "空闲", "占用账号": "", "是否禁用": False})
            for id in 新设备IDs
        ]
        self.发送设备状态()

    def 禁用设备(self, 数据):
        设备ID = 数据.get("设备ID") if isinstance(数据, dict) else None
        if not 设备ID:
            return
        for 设备 in self.设备列表:
            if 设备["设备ID"] == 设备ID:
                if 设备["状态"] != "空闲":
                    return  # 占用中不允许禁用，只有空闲可以
                设备["是否禁用"] = True
                设备["状态"] = "禁用"
                self.发送设备状态()
                return

    def 启用设备(self, 数据):
        设备ID = 数据.get("设备ID") if isinstance(数据, dict) else None
        if not 设备ID:
            return
        for 设备 in self.设备列表:
            if 设备["设备ID"] == 设备ID:
                设备["是否禁用"] = False
                # 若禁用时正被占用，启用后恢复为占用；否则为空闲
                设备["状态"] = "占用" if 设备.get("占用账号") else "空闲"
                self.发送设备状态()
                # 启用后若有设备变空闲，让等待队列中的账号使用
                self._处理等待队列()
                return

    def 获取空闲设备(self):
        for 设备 in self.设备列表:
            if 设备.get("是否禁用"):
                continue
            if 设备["状态"] == "空闲":
                return 设备["设备ID"]
        return None

    def 查找账号设备(self, 账号key):
        for 设备 in self.设备列表:
            if 设备["占用账号"] == 账号key:
                return 设备["设备ID"]
        return None

    def 分配设备(self, 设备ID, 账号key):
        for 设备 in self.设备列表:
            if 设备["设备ID"] == 设备ID:
                设备["状态"] = "占用"
                设备["占用账号"] = 账号key
                return

    def 释放设备(self, 设备ID):
        for 设备 in self.设备列表:
            if 设备["设备ID"] == 设备ID:
                设备["状态"] = "空闲"
                设备["占用账号"] = ""
                return

    def 发送设备状态(self):
        self.发送到Electron("device-list", self.设备列表)

    # ─── 任务列表 ──────────────────────────────

    def 获取任务列表(self):
        任务列表 = 发现所有任务模块()
        self.发送到Electron("task-list", list(任务列表.keys()))

    # ─── 账号管理 ──────────────────────────────

    def 读取账号列表(self):
        try:
            with open(账号文件路径, "r", encoding="utf-8") as f:
                列表 = json.load(f)
            return 列表 if isinstance(列表, list) else []
        except Exception:
            return []

    def 发送账号列表(self):
        self.发送到Electron("account-list", self.读取账号列表())

    # ─── 账号任务操作 ──────────────────────────

    def 账号开始任务(self, 数据):
        账号key = 数据.get("账号")
        if not 账号key:
            return

        with self._池锁:
            if self.查找账号设备(账号key):
                self.更新账号数据(账号key, "日志", "任务已在运行中")
                return
            if any(k == 账号key for k, _ in self.等待队列):
                self.更新账号数据(账号key, "日志", "已在等待队列中")
                return

            设备ID = self.获取空闲设备()
            if 设备ID:
                self._启动账号任务(账号key, 设备ID, 数据)
            else:
                self.等待队列.append((账号key, 数据))
                self.更新账号数据(账号key, "状态", "等待设备")
                self.更新账号数据(账号key, "日志", "没有空闲设备，排队等待中...")

    def _启动账号任务(self, 账号key, 设备ID, 数据):
        """将设备分配给账号并启动线程（调用前需持有 _池锁）"""
        self.分配设备(设备ID, 账号key)
        数据["设备ID"] = 设备ID
        数据["更新数据"] = lambda 字段=None, 数据=None: self.更新账号数据(账号key, 字段, 数据)
        self.线程控制器.启动线程(线程key=账号key, 任务函数参数集合=数据)
        self.更新账号数据(账号key, "设备ID", 设备ID)
        self.更新账号数据(账号key, "状态", "运行中")
        self.发送设备状态()

    def 账号结束任务(self, 数据):
        账号key = 数据.get("账号")
        if not 账号key:
            return
        with self._池锁:
            self.等待队列 = [(k, d) for k, d in self.等待队列 if k != 账号key]
        if self.查找账号设备(账号key):
            self.线程控制器.停止线程(账号key)
        else:
            self.更新账号数据(账号key, "状态", "空闲")
            self.更新账号数据(账号key, "设备ID", "")

    def 账号暂停任务(self, 数据):
        账号key = 数据.get("账号")
        if 账号key and self.查找账号设备(账号key):
            self.线程控制器.暂停线程(账号key)
            self.更新账号数据(账号key, "状态", "已暂停")

    def 账号恢复任务(self, 数据):
        账号key = 数据.get("账号")
        if 账号key and self.查找账号设备(账号key):
            self.线程控制器.恢复线程(账号key)
            self.更新账号数据(账号key, "状态", "运行中")

    def 全部开始(self, 数据):
        账号列表 = self.读取账号列表()
        任务队列 = 数据.get("任务队列", [])
        任务配置 = 数据.get("任务配置", [])
        for 账号 in 账号列表:
            self.账号开始任务({
                "账号": 账号.get("账号"),
                "任务队列": list(任务队列),
                "任务配置": list(任务配置),
            })

    def 全部结束(self):
        with self._池锁:
            等待中的账号 = [k for k, _ in self.等待队列]
            self.等待队列.clear()
        for 账号key in 等待中的账号:
            self.更新账号数据(账号key, "状态", "空闲")
            self.更新账号数据(账号key, "设备ID", "")
        self.线程控制器.停止全部线程()

    def 全部暂停(self):
        self.线程控制器.暂停全部线程()
        for 设备 in self.设备列表:
            if 设备["状态"] == "占用":
                self.更新账号数据(设备["占用账号"], "状态", "已暂停")

    def 全部恢复(self):
        self.线程控制器.恢复全部线程()
        for 设备 in self.设备列表:
            if 设备["状态"] == "占用":
                self.更新账号数据(设备["占用账号"], "状态", "运行中")

    # ─── 回调 ──────────────────────────────────

    def 线程结束回调(self, 账号key):
        with self._池锁:
            设备ID = self.查找账号设备(账号key)
            if 设备ID:
                self.释放设备(设备ID)
        self.更新账号数据(账号key, "状态", "空闲")
        self.更新账号数据(账号key, "设备ID", "")
        self.更新账号数据(账号key, "当前任务", "")
        self.发送设备状态()
        self._处理等待队列()

    def _处理等待队列(self):
        with self._池锁:
            while self.等待队列:
                设备ID = self.获取空闲设备()
                if not 设备ID:
                    break
                账号key, 数据 = self.等待队列.pop(0)
                self._启动账号任务(账号key, 设备ID, 数据)

    def 更新账号数据(self, 账号key, 字段, 数据):
        if 字段 == "日志":
            self.日志管理器.写入日志(账号key, 数据)
        self.发送到Electron("account-status-update", {
            "账号": 账号key,
            字段: 数据,
        })


if __name__ == "__main__":
    主程序()
