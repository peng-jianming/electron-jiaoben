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

# 账号(无绑定) -> 等待设备空闲(随意设备) -> 运行,
# 账号(绑定设备) -> 等待设备空闲(绑定的那台) -> 运行

class 主程序:
    def __init__(self):
        self.日志管理器 = 日志管理器类(日志目录)
        self.账号管理器 = 账号管理器类(账号文件路径)
        self._池锁 = threading.Lock()
        self.等待队列 = []           # [(id_key, 数据dict)]
        self._id到账号名 = {}        # {id_key: 账号显示名} 用于日志文件命名

        self.线程控制器 = 线程控制器类(
            回调函数=任务管理器类,
            线程结束后回调函数=self.线程结束回调,
            打印回调函数=self.更新账号数据,
        )

        self.设备池管理器 = 设备池管理器类(self._发送设备状态到前端)

        self.通信管理器 = 通信管理器类(
            服务器地址=服务器地址,
            消息处理回调=self.客户端消息队列处理,
        )

    def _刷新id映射(self, 账号列表=None):
        """从账号列表刷新 id → 账号显示名 的映射，用于日志文件命名。"""
        if 账号列表 is None:
            账号列表 = self.账号管理器.获取账号列表()
        for 项 in 账号列表:
            self._id到账号名[项["id"]] = 项.get("账号")

    def _发送账号列表(self):
        账号列表 = self.账号管理器.获取账号列表()
        self._刷新id映射(账号列表)
        self.通信管理器.发送到Electron("account-list", 账号列表)

    def _刷新设备列表并调度(self, _数据=None):
        """ADB 刷新设备池后，尝试为等待队列中的账号分配设备（含刚连上的绑定设备）。"""
        self.设备池管理器.获取设备列表()
        self.处理账号等待队列()

    def 客户端消息队列处理(self, 类型, 数据):
        """供通信管理器在消息队列线程中回调，处理单条消息。"""
        处理器 = {
            "打开日志": lambda d: self.日志管理器.打开日志(d.get("账号")),
            "获取设备列表": self._刷新设备列表并调度,
            "获取任务列表": lambda d: self.通信管理器.发送到Electron("task-list",list(任务管理器类.获取所有任务列表().keys())),
            "获取账号列表": lambda d: self._发送账号列表(),
            "重置账号任务进度": lambda d: self._重置账号任务进度(d.get("id")),
            "禁用设备": lambda d: self.设备池管理器.禁用设备(d.get("设备ID")),
            "启用设备": lambda d: self.设备池管理器.启用设备(d.get("设备ID")) and self.处理账号等待队列(),
            "绑定设备": self.绑定设备,
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

    def _重置账号任务进度(self, id_key):
        """重置账号的任务进度为 0。"""
        if not id_key:
            return
        self.账号管理器.写入账号列表(id_key, "任务进度", 0)
        self.更新账号数据(id_key, "任务进度", 0)
        self.更新账号数据(id_key, "状态", "空闲")
        self.更新账号数据(id_key, "日志", "任务进度已重置")

    def 绑定设备(self, 数据):
        """前端请求绑定/解绑设备：将指定账号的绑定设备写入持久化并通知前端。"""
        id_key = 数据.get("id")
        设备ID = 数据.get("绑定设备", "")
        if not id_key:
            return
        self.账号管理器.写入账号列表(id_key, "绑定设备", 设备ID)
        self.通信管理器.发送到Electron(
            "account-status-update",
            {"id": id_key, "绑定设备": 设备ID},
        )

    def _获取账号绑定设备(self, id_key):
        """从账号列表获取该账号绑定的设备ID，未绑定返回空字符串。"""
        账号列表 = self.账号管理器.获取账号列表()
        for 项 in 账号列表:
            if 项.get("id") == id_key:
                return 项.get("绑定设备", "")
        return ""

    def 账号开始任务(self, 数据):
        id_key = 数据.get("id")
        任务配置列表 = 数据.get("任务配置列表", [])
        if not id_key:
            return

        任务进度 = self.账号管理器.获取任务进度(id_key)

        if 任务进度 >= len(任务配置列表):
            return

        数据["任务进度"] = 任务进度

        绑定设备 = self._获取账号绑定设备(id_key)
        数据["绑定设备"] = 绑定设备

        with self._池锁:
            if self.设备池管理器.查找账号设备(id_key):
                self.更新账号数据(id_key, "日志", "任务已在运行中")
                return
            if any(k == id_key for k, _ in self.等待队列):
                self.更新账号数据(id_key, "日志", "已在等待队列中")
                return

            if 绑定设备:
                if not self.设备池管理器.设备是否在池中(绑定设备):
                    self.等待队列.append((id_key, 数据))
                    self.更新账号数据(id_key, "状态", "等待设备")
                    self.更新账号数据(
                        id_key,
                        "日志",
                        f"绑定设备未连接（{绑定设备} 不在当前设备池），请连接 USB 后点「刷新设备」",
                    )
                elif self.设备池管理器.指定设备是否空闲(绑定设备):
                    self._启动账号任务(id_key, 绑定设备, 数据)
                else:
                    条目 = self.设备池管理器.获取设备条目(绑定设备)
                    已禁用 = 条目 and (
                        条目.get("是否禁用") or 条目.get("状态") == "禁用"
                    )
                    self.等待队列.append((id_key, 数据))
                    self.更新账号数据(id_key, "状态", "等待设备")
                    if 已禁用:
                        self.更新账号数据(
                            id_key,
                            "日志",
                            f"绑定设备 {绑定设备} 已禁用，请启用后再运行",
                        )
                    else:
                        self.更新账号数据(
                            id_key,
                            "日志",
                            f"绑定设备 {绑定设备} 忙碌中，排队等待...",
                        )
            else:
                设备ID = self.设备池管理器.获取空闲设备()
                if 设备ID:
                    self._启动账号任务(id_key, 设备ID, 数据)
                else:
                    self.等待队列.append((id_key, 数据))
                    self.更新账号数据(id_key, "状态", "等待设备")
                    self.更新账号数据(id_key, "日志", "没有空闲设备，排队等待中...")

    def _启动账号任务(self, id_key, 设备ID, 数据):
        """将设备分配给账号并启动线程（调用前需持有 _池锁）"""
        self.设备池管理器.分配设备(设备ID, id_key)
        数据["设备ID"] = 设备ID
        数据["更新数据"] = lambda 字段=None, 数据=None: self.更新账号数据(id_key, 字段, 数据)
        self.线程控制器.启动线程(线程key=id_key, 任务函数参数集合=数据)
        self.更新账号数据(id_key, "设备ID", 设备ID)
        self.更新账号数据(id_key, "状态", "运行中")

    def 账号结束任务(self, 数据):
        id_key = 数据.get("id")
        if not id_key:
            return
        with self._池锁:
            self.等待队列 = [(k, d) for k, d in self.等待队列 if k != id_key]
        if self.设备池管理器.查找账号设备(id_key):
            self.线程控制器.停止线程(id_key)

    def 账号暂停任务(self, 数据):
        id_key = 数据.get("id")
        if id_key and self.设备池管理器.查找账号设备(id_key):
            self.线程控制器.暂停线程(id_key)
            self.更新账号数据(id_key, "状态", "已暂停")

    def 账号恢复任务(self, 数据):
        id_key = 数据.get("id")
        if id_key and self.设备池管理器.查找账号设备(id_key):
            self.线程控制器.恢复线程(id_key)
            self.更新账号数据(id_key, "状态", "运行中")

    def 全部开始(self, 数据):
        账号列表 = self.账号管理器.获取账号列表()
        self._刷新id映射(账号列表)
        任务配置列表 = 数据.get("任务配置列表", [])
        for 账号 in 账号列表:
            self.账号开始任务({
                "id": 账号.get("id"),
                "任务配置列表": [dict(t) for t in 任务配置列表],
                "任务进度": 账号.get("任务进度", 0),
            })

    def 全部结束(self):
        with self._池锁:
            等待中 = [k for k, _ in self.等待队列]
            self.等待队列.clear()
        for id_key in 等待中:
            self.更新账号数据(id_key, "状态", "空闲")
            self.更新账号数据(id_key, "设备ID", "")
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

    def 线程结束回调(self, id_key):
        with self._池锁:
            设备ID = self.设备池管理器.查找账号设备(id_key)
            if 设备ID:
                self.设备池管理器.释放设备(设备ID)

        self.更新账号数据(id_key, "设备ID", "")
        self.更新账号数据(id_key, "状态", "空闲")
        self.处理账号等待队列()

    def 处理账号等待队列(self):
        """
        调度等待队列中的账号到空闲设备：
        对每台空闲设备，优先分配绑定了该设备的账号，其次分配未绑定的账号。
        绑定了其他设备的账号只能等待自己绑定的那台。
        """
        with self._池锁:
            while self.等待队列:
                空闲设备列表 = self.设备池管理器.获取所有空闲设备()
                if not 空闲设备列表:
                    break

                本轮已分配 = False
                for 设备ID in 空闲设备列表:
                    绑定索引 = next(
                        (i for i, (_, d) in enumerate(self.等待队列)
                         if d.get("绑定设备") == 设备ID),
                        None,
                    )
                    if 绑定索引 is not None:
                        id_key, 数据 = self.等待队列.pop(绑定索引)
                        self._启动账号任务(id_key, 设备ID, 数据)
                        本轮已分配 = True
                        break

                    未绑定索引 = next(
                        (i for i, (_, d) in enumerate(self.等待队列)
                         if not d.get("绑定设备")),
                        None,
                    )
                    if 未绑定索引 is not None:
                        id_key, 数据 = self.等待队列.pop(未绑定索引)
                        self._启动账号任务(id_key, 设备ID, 数据)
                        本轮已分配 = True
                        break

                if not 本轮已分配:
                    break

    def _发送设备状态到前端(self, 设备列表):
        """供设备池管理器回调，将设备列表推送到前端。"""
        self.通信管理器.发送到Electron("device-list", 设备列表)

    def 更新账号数据(self, id_key, 字段, 数据):
        if 字段 == "日志":
            账号名 = self._id到账号名.get(id_key)
            self.日志管理器.写入日志(账号名, 数据)
        self.账号管理器.写入账号列表(id_key, 字段, 数据)
        self.通信管理器.发送到Electron(
            "account-status-update",
            {
                "id": id_key,
                字段: 数据,
            },
        )


if __name__ == "__main__":
    主程序()
