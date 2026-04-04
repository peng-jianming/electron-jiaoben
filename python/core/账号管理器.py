"""
账号管理器：负责账号列表的持久化（JSON 文件）读写与按 id/字段更新。
每条账号记录拥有系统自动生成的唯一 id，所有查找和写入均以 id 为主键。
"""

import json
import os
import uuid


class 账号管理器类:
    _持久化字段白名单 = {"id", "账号", "区服", "名字", "等级", "门派", "金币", "任务进度", "绑定设备"}

    def __init__(self, 账号文件路径):
        self.账号文件路径 = 账号文件路径

    @staticmethod
    def _条目账号有效(项):
        """有「账号」键且为去掉空白后非空的字符串才保留。"""
        if not isinstance(项, dict):
            return False
        账号 = 项.get("账号")
        if not isinstance(账号, str):
            return False
        return bool(账号.strip())

    def 获取账号列表(self, 强制从文件=False):
        try:
            if not os.path.exists(self.账号文件路径):
                return []
            with open(self.账号文件路径, "r", encoding="utf-8") as f:
                列表 = json.load(f)
            if not isinstance(列表, list):
                return []
            剔除前长度 = len(列表)
            列表 = [项 for 项 in 列表 if self._条目账号有效(项)]
            已迁移 = 剔除前长度 != len(列表)
            for 项 in 列表:
                if not isinstance(项, dict):
                    continue
                if "id" not in 项:
                    项["id"] = uuid.uuid4().hex[:8]
                    已迁移 = True
                if "任务进度" not in 项:
                    项["任务进度"] = 0
                    已迁移 = True
            if 已迁移:
                self._保存列表(列表)
            return 列表
        except Exception:
            return []

    def 获取任务进度(self, id):
        列表 = self.获取账号列表()
        for 项 in 列表:
            if isinstance(项, dict) and 项.get("id") == id:
                return 项.get("任务进度", 0)
        return 0

    def 写入账号列表(self, id, 字段, 内容):
        """
        更新指定 id 账号的某个字段并写回文件。仅白名单中的字段才会持久化。
        """
        if 字段 not in self._持久化字段白名单:
            return
        列表 = self.获取账号列表()
        for 项 in 列表:
            if not isinstance(项, dict):
                continue
            if 项.get("id") == id:
                项[字段] = 内容
                self._保存列表(列表)
                return

    def _保存列表(self, 列表):
        """将账号列表写入文件。"""
        try:
            目录 = os.path.dirname(self.账号文件路径)
            if 目录:
                os.makedirs(目录, exist_ok=True)
            with open(self.账号文件路径, "w", encoding="utf-8") as f:
                json.dump(列表, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"保存账号列表失败: {e}") from e
