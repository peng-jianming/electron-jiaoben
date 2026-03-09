from .ADB控制器 import ADB控制器类


class 设备池管理器类:
    """
    设备池管理器：
    - 负责维护设备列表（设备ID / 状态 / 占用账号 / 是否禁用）
    - 封装刷新、禁用/启用、分配/释放等操作
    - 通过 回调函数 将最新设备列表推送给上层（通常是发往前端）
    """

    def __init__(self, 发送设备状态回调):
        self._设备列表 = []
        self._发送设备状态回调 = 发送设备状态回调

    @property
    def 设备列表(self):
        return self._设备列表

    def 获取设备列表(self):
        """从 ADB 获取最新设备列表，并保持已有状态信息。"""
        adb = ADB控制器类()
        新设备IDs = adb.获取设备列表()
        已有映射 = {d["设备ID"]: d for d in self._设备列表}
        self._设备列表 = [
            已有映射.get(
                设备ID,
                {
                    "设备ID": 设备ID,
                    "状态": "空闲",
                    "占用账号": "",
                    "是否禁用": False,
                },
            )
            for 设备ID in 新设备IDs
        ]
        self._推送设备状态()

    def 禁用设备(self, 设备ID):
        """仅当设备处于空闲状态时才允许禁用。"""
        if not 设备ID:
            return
        for 设备 in self._设备列表:
            if 设备["设备ID"] == 设备ID:
                if 设备["状态"] != "空闲":
                    return
                设备["是否禁用"] = True
                设备["状态"] = "禁用"
                self._推送设备状态()
                return

    def 启用设备(self, 设备ID):
        """启用设备：根据是否有占用账号恢复为 占用 或 空闲 状态。"""
        if not 设备ID:
            return False
        for 设备 in self._设备列表:
            if 设备["设备ID"] == 设备ID:
                设备["是否禁用"] = False
                设备["状态"] = "占用" if 设备.get("占用账号") else "空闲"
                self._推送设备状态()
                return True

    def 获取空闲设备(self):
        """返回一个未禁用且状态为空闲的设备ID，找不到则返回 None。"""
        for 设备 in self._设备列表:
            if 设备.get("是否禁用"):
                continue
            if 设备["状态"] == "空闲":
                return 设备["设备ID"]
        return None

    def 查找账号设备(self, 账号key):
        """根据账号key 查找其占用的设备ID。"""
        for 设备 in self._设备列表:
            if 设备["占用账号"] == 账号key:
                return 设备["设备ID"]
        return None

    def 分配设备(self, 设备ID, 账号key):
        """将设备标记为被指定账号占用。"""
        if not 设备ID or not 账号key:
            return
        for 设备 in self._设备列表:
            if 设备["设备ID"] == 设备ID:
                设备["状态"] = "占用"
                设备["占用账号"] = 账号key
                self._推送设备状态()
                return

    def 释放设备(self, 设备ID):
        """释放设备占用，将其恢复为空闲。"""
        if not 设备ID:
            return
        for 设备 in self._设备列表:
            if 设备["设备ID"] == 设备ID:
                设备["状态"] = "空闲"
                设备["占用账号"] = ""
                self._推送设备状态()
                return

    def _推送设备状态(self):
        if self._发送设备状态回调:
            try:
                self._发送设备状态回调(self._设备列表)
            except Exception as e:
                print(f"推送设备状态回调异常: {e}")

