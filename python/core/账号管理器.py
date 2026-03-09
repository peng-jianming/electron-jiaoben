"""
账号管理器：负责账号列表的持久化（JSON 文件）读写与按账号/字段更新。
"""

import json
import os


class 账号管理器类:
    def __init__(self, 账号文件路径):
        self.账号文件路径 = 账号文件路径
        self._缓存列表 = None  # 内存缓存，避免每次写入都读文件

    def 获取账号列表(self, 强制从文件=False):
        """
        从配置文件读取账号列表，返回 list；文件不存在或格式错误时返回 []。
        :param 强制从文件: 为 True 时忽略缓存，重新从文件读取（用于外部修改文件后刷新）
        """
        if not 强制从文件 and self._缓存列表 is not None:
            return self._缓存列表
        try:
            if not os.path.exists(self.账号文件路径):
                self._缓存列表 = []
                return []
            with open(self.账号文件路径, "r", encoding="utf-8") as f:
                列表 = json.load(f)
            self._缓存列表 = 列表 if isinstance(列表, list) else []
            return self._缓存列表
        except Exception:
            self._缓存列表 = []
            return []

    def 写入账号列表(self, 账号, 字段, 内容):
        """
        更新指定账号的某个字段并写回文件。仅当该项已存在该字段时才写入，未定义的属性不会新增。
        :param 账号: 账号唯一标识（与列表中某项的 "账号" 字段一致）
        :param 字段: 要更新的字段名
        :param 内容: 新值
        """
        列表 = self.获取账号列表()  # 有缓存时不再打开文件
        for 项 in 列表:
            if not isinstance(项, dict):
                continue
            if 项.get("账号") == 账号:
                if 字段 in 项:  # 只有已定义的属性才允许写入
                    项[字段] = 内容
                    self._保存列表(列表)
                return
        # 未找到则忽略（或可改为追加一条新记录，按需求再扩展）

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

