"""
无窗口视频帧：基于 PyPI「scrcpy-core」的 scrcpy.Client（包内自带 scrcpy-server 3.1 jar，adbutils + PyAV 解码）。

- 不再需要项目里的 python/scrcpy 目录或 OpenCV 拉 tcp 流。
- 解码在后台线程持续更新 last_frame，低频取帧时天然接近「当前最新画面」。
- 仍会与正在运行的其它 scrcpy / 群控争用同一设备，请关闭后再连。
"""
from __future__ import annotations

import os
import time
from typing import Optional

import numpy as np

from 设置 import ADB路径, 项目根目录

# 让 adbutils 能找到与「设置.ADB路径」一致的 adb.exe（须在 import scrcpy 之前）
def _ensure_adb_path_for_adbutils() -> None:
    p = ADB路径.strip('"').strip()
    if not p or p.lower() == "adb":
        return
    if os.path.isfile(p):
        adb_dir = os.path.dirname(os.path.abspath(p))
        os.environ["PATH"] = adb_dir + os.pathsep + os.environ.get("PATH", "")


_ensure_adb_path_for_adbutils()

try:
    from scrcpy import Client
except ImportError as e:
    raise ImportError(
        "请先安装 scrcpy-core：在 python 目录执行 pip install -r requirements.txt"
    ) from e

_DEFAULT_SCRCPY_DIR = os.path.join(项目根目录, "scrcpy")


class Scrcpy视频流类:
    """上下文管理器：进入后开始推流，退出时停止 Client。"""

    def __init__(
        self,
        设备ID: Optional[str] = None,
        scrcpy目录: Optional[str] = None,
        本机端口: Optional[int] = None,
        max_size: Optional[int] = None,
        video_bit_rate: Optional[int] = None,
    ):
        """
        :param scrcpy目录: 已忽略（保留参数仅为兼容旧调用）；服务端 jar 由 scrcpy-core 自带。
        :param 本机端口: 已忽略（保留参数仅为兼容旧调用）。
        :param max_size: 长边上限（像素）。None 或 0 表示由库默认（通常即不缩小或按库内默认）。
        :param video_bit_rate: H.264 码率；None 使用 scrcpy-core 默认 8Mbps。
        """
        self.设备ID = 设备ID
        self.scrcpy目录 = scrcpy目录 or _DEFAULT_SCRCPY_DIR
        self.max_size = 0 if max_size is None else int(max_size)
        self.video_bit_rate = (
            int(video_bit_rate) if video_bit_rate is not None else 8_000_000
        )
        self._client: Optional[Client] = None
        self._已启动 = False

    def 开始(self) -> None:
        if self._已启动:
            return
        self._client = Client(
            device=self.设备ID,
            max_width=self.max_size,
            bitrate=self.video_bit_rate,
            max_fps=0,
        )
        self._client.start(daemon_threaded=True)
        self._已启动 = True
        # 首帧到达前 last_frame 可能为 None
        deadline = time.time() + 15.0
        while time.time() < deadline:
            if self._client.last_frame is not None:
                break
            time.sleep(0.05)
        else:
            self.停止()
            raise RuntimeError(
                "scrcpy-core 在超时内未收到首帧。请关闭其它 scrcpy/群控，检查 USB 调试与 adb devices。"
            )

    def 停止(self) -> None:
        if self._client is not None:
            try:
                self._client.stop()
            except Exception:
                pass
            self._client = None
        self._已启动 = False

    def 读取一帧(self, 丢弃旧帧: bool = True, 最多丢弃: int = 256):
        """
        返回当前解码得到的最新一帧（BGR ndarray 的副本）；尚无画面时返回 None。

        使用 scrcpy-core 时画面在后台线程更新，last_frame 即为最新，「丢弃旧帧 / 最多丢弃」
        仅保留与旧 API 兼容，不再触发 OpenCV 队列排空。
        """
        # 丢弃旧帧、最多丢弃：兼容旧 API；scrcpy-core 用后台线程更新 last_frame，无 OpenCV 队列。
        _ = (丢弃旧帧, 最多丢弃)
        if not self._已启动 or self._client is None:
            raise RuntimeError("请先调用 开始() 或 使用 with Scrcpy视频流类(...) as s:")
        f = self._client.last_frame
        if f is None:
            return None
        return np.ascontiguousarray(f)

    def __enter__(self) -> "Scrcpy视频流类":
        self.开始()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.停止()
        return False
