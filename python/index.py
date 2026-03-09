"""
群控图色脚本 Python 后端入口
通过 Socket.IO 与 Electron 前端通信
以账号为主体，动态从设备池中分配空闲设备运行任务。
"""

import threading
from 设置 import 服务器地址, 账号文件路径, 日志目录
from core.线程控制器 import 线程控制器类
from core.任务管理器 import 任务管理器类
from core.日志管理器 import 日志管理器类
from core.账号管理器 import 账号管理器类
from core.通信管理器 import 通信管理器类
from core.设备池管理器 import 设备池管理器类

class 主程序:
    def __init__(self):
        self.日志管理器 = 日志管理器类(日志目录)
        self.账号管理器 = 账号管理器类(账号文件路径)
        self._池锁 = threading.Lock()
        self.等待队列 = []           # [(账号key, 数据dict)]

        # 线程控制器：负责账号任务线程
        self.线程控制器 = 线程控制器类(
            回调函数=任务管理器类,
            线程结束后回调函数=self.线程结束回调,
            打印回调函数=self.更新账号数据,
        )

        # 设备池管理器：负责设备列表及状态维护
        self.设备池管理器 = 设备池管理器类(self._发送设备状态到前端)

        # 通信管理器：负责 socket.io 连接、消息转发与队列处理
        self.通信管理器 = 通信管理器类(
            服务器地址=服务器地址,
            消息处理回调=self.客户端消息队列处理,
        )

    def 客户端消息队列处理(self, 类型, 数据):
        """供通信管理器在消息队列线程中回调，处理单条消息。"""
        处理器 = {
            "打开日志": lambda d: self.日志管理器.打开日志(d.get("账号")),
            "获取设备列表": lambda d: self.设备池管理器.获取设备列表(),
            "获取任务列表": lambda d: self.通信管理器.发送到Electron("task-list", 任务管理器类.获取所有任务列表().keys()),
            "获取账号列表": lambda d: self.通信管理器.发送到Electron("account-list", self.账号管理器.获取账号列表()),
            "禁用设备": lambda d: self.设备池管理器.禁用设备(d.get("设备ID")),
            "启用设备": lambda d: self.设备池管理器.启用设备(d.get("设备ID")) and self.处理账号等待队列(),
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

    # ─── 账号任务操作 ──────────────────────────

    def 账号开始任务(self, 数据):
        账号key = 数据.get("账号")
        if not 账号key:
            return

        with self._池锁:
            if self.设备池管理器.查找账号设备(账号key):
                self.更新账号数据(账号key, "日志", "任务已在运行中")
                return
            if any(k == 账号key for k, _ in self.等待队列):
                self.更新账号数据(账号key, "日志", "已在等待队列中")
                return

            设备ID = self.设备池管理器.获取空闲设备()
            if 设备ID:
                self._启动账号任务(账号key, 设备ID, 数据)
            else:
                self.等待队列.append((账号key, 数据))
                self.更新账号数据(账号key, "状态", "等待设备")
                self.更新账号数据(账号key, "日志", "没有空闲设备，排队等待中...")

    def _启动账号任务(self, 账号key, 设备ID, 数据):
        """将设备分配给账号并启动线程（调用前需持有 _池锁）"""
        self.设备池管理器.分配设备(设备ID, 账号key)
        数据["设备ID"] = 设备ID
        数据["更新数据"] = lambda 字段=None, 数据=None: self.更新账号数据(账号key, 字段, 数据)
        self.线程控制器.启动线程(线程key=账号key, 任务函数参数集合=数据)
        self.更新账号数据(账号key, "设备ID", 设备ID)
        self.更新账号数据(账号key, "状态", "运行中")

    def 账号结束任务(self, 数据):
        账号key = 数据.get("账号")
        if not 账号key:
            return
        with self._池锁:
            self.等待队列 = [(k, d) for k, d in self.等待队列 if k != 账号key]
        if self.设备池管理器.查找账号设备(账号key):
            self.线程控制器.停止线程(账号key)
        else:
            self.更新账号数据(账号key, "状态", "空闲")
            self.更新账号数据(账号key, "设备ID", "")

    def 账号暂停任务(self, 数据):
        账号key = 数据.get("账号")
        if 账号key and self.设备池管理器.查找账号设备(账号key):
            self.线程控制器.暂停线程(账号key)
            self.更新账号数据(账号key, "状态", "已暂停")

    def 账号恢复任务(self, 数据):
        账号key = 数据.get("账号")
        if 账号key and self.设备池管理器.查找账号设备(账号key):
            self.线程控制器.恢复线程(账号key)
            self.更新账号数据(账号key, "状态", "运行中")

    def 全部开始(self, 数据):
        账号列表 = self.账号管理器.获取账号列表()
        任务配置列表 = 数据.get("任务配置列表", [])
        for 账号 in 账号列表:
            账号自带配置 = 账号.get("任务配置列表", [])
            self.账号开始任务({
                "账号": 账号.get("账号"),
                "任务配置列表": list(账号自带配置) if 账号自带配置 else [dict(t) for t in 任务配置列表],
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
        for 设备 in self.设备池管理器.设备列表:
            if 设备["状态"] == "占用":
                self.更新账号数据(设备["占用账号"], "状态", "已暂停")

    def 全部恢复(self):
        self.线程控制器.恢复全部线程()
        for 设备 in self.设备池管理器.设备列表:
            if 设备["状态"] == "占用":
                self.更新账号数据(设备["占用账号"], "状态", "运行中")

    # ─── 回调 ──────────────────────────────────

    def 线程结束回调(self, 账号key):
        with self._池锁:
            设备ID = self.设备池管理器.查找账号设备(账号key)
            if 设备ID:
                self.设备池管理器.释放设备(设备ID)
        self.更新账号数据(账号key, "状态", "空闲")
        self.更新账号数据(账号key, "设备ID", "")
        self.更新账号数据(账号key, "当前任务", "")
        self.处理账号等待队列()

    def 处理账号等待队列(self):
        with self._池锁:
            while self.等待队列:
                设备ID = self.设备池管理器.获取空闲设备()
                if not 设备ID:
                    break
                账号key, 数据 = self.等待队列.pop(0)
                self._启动账号任务(账号key, 设备ID, 数据)

    def _发送设备状态到前端(self, 设备列表):
        """供设备池管理器回调，将设备列表推送到前端。"""
        self.通信管理器.发送到Electron("device-list", 设备列表)

    def 更新账号数据(self, 账号key, 字段, 数据):
        if 字段 == "日志":
            self.日志管理器.写入日志(账号key, 数据)
        self.账号管理器.写入账号列表(账号key, 字段, 数据)
        self.通信管理器.发送到Electron(
            "account-status-update",
            {
                "账号": 账号key,
                字段: 数据,
            },
        )


if __name__ == "__main__":
    主程序()
