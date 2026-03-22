"""
视频帧（低延迟）：通过 scrcpy-core（内置 scrcpy 3.1 服务端 + PyAV）取流，不弹投屏窗口。
备用：可用项目内 ADB 截图（较慢）。
"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.abspath(__file__))
_PYTHON = os.path.join(_ROOT, "python")
if _PYTHON not in sys.path:
    sys.path.insert(0, _PYTHON)

import cv2
import numpy as np
from PIL import Image

from core.Scrcpy视频流 import Scrcpy视频流类
from 设置 import 缓存目录

_DEFAULT_SCRCPY_DIR = os.path.join(_ROOT, "python", "scrcpy")
_DEFAULT_DEBUG_DIR = os.path.join(缓存目录, "aaa调试截图")


class 设备视频流会话类:
    """
    绑定一台设备，通过 scrcpy-core 建立视频流后，可反复调用 获取当前视频帧()（无需每次重连）。

    用法::

        cam = 设备视频流会话类("9a8de478")
        cam.开始()
        try:
            for _ in range(100):
                bgr = cam.获取当前视频帧()
        finally:
            cam.关闭()

    或使用 with::

        with 设备视频流会话类("9a8de478") as cam:
            bgr = cam.获取当前视频帧()
    """

    def __init__(
        self,
        设备ID,
        *,
        scrcpy目录=None,
        max_size=None,
        video_bit_rate=16_000_000,
        本机端口=None,
    ):
        self.设备ID = 设备ID
        self._流 = None
        self._kw = dict(
            设备ID=设备ID,
            scrcpy目录=scrcpy目录 or _DEFAULT_SCRCPY_DIR,
            max_size=max_size,
            video_bit_rate=video_bit_rate,
            本机端口=本机端口,
        )

    def 开始(self) -> None:
        if self._流 is not None:
            return
        self._流 = Scrcpy视频流类(**self._kw)
        self._流.开始()

    def 关闭(self) -> None:
        if self._流 is not None:
            self._流.停止()
            self._流 = None

    @property
    def 已连接(self) -> bool:
        return self._流 is not None and getattr(self._流, "_已启动", False)

    def 获取当前视频帧(self, 丢弃旧帧=True, 最多丢弃=256):
        """
        取尽量新的一帧 BGR ndarray；未启动时会自动 开始()。
        流断开或解码失败时返回 None。

        间隔较久再取帧时，应保留默认 丢弃旧帧=True，否则会读到解码队列里的旧画面。
        """
        self.开始()
        return self._流.读取一帧(丢弃旧帧=丢弃旧帧, 最多丢弃=最多丢弃)

    def __enter__(self):
        self.开始()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.关闭()
        return False


def _调试输出截图(
    图像,
    *,
    前缀="帧",
    保存目录=None,
    显示窗口=False,
    保存格式="bmp",
):
    """
    将 BGR ndarray 或 PIL(RGB) 落盘；默认 BMP（无压缩位图，体积大但无保存损）。
    保存格式 \"png\" 时为无损 PNG（zlib 仅打包像素，不改变画质）。
    """
    目录 = 保存目录 or _DEFAULT_DEBUG_DIR
    os.makedirs(目录, exist_ok=True)
    fmt = (保存格式 or "bmp").lower().lstrip(".")
    if fmt not in ("bmp", "png"):
        fmt = "bmp"
    名 = time.strftime(f"{前缀}_%Y%m%d_%H%M%S.{fmt}")
    路径 = os.path.abspath(os.path.join(目录, "1.png"))

    if isinstance(图像, np.ndarray):
        预览 = 图像
        if fmt == "bmp":
            ok, buf = cv2.imencode(".bmp", 图像)
        else:
            ok, buf = cv2.imencode(
                ".png",
                图像,
                [cv2.IMWRITE_PNG_COMPRESSION, 0],
            )
        if not ok:
            print(f"[调试] {fmt.upper()} 编码失败，未写入文件")
            return
        with open(路径, "wb") as f:
            f.write(buf.tobytes())
    elif isinstance(图像, Image.Image):
        rgb = 图像.convert("RGB")
        预览 = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
        with open(路径, "wb") as f:
            if fmt == "bmp":
                rgb.save(f, format="BMP")
            else:
                rgb.save(f, format="PNG", compress_level=0)
    else:
        print(f"[调试] 不支持的图像类型: {type(图像)}")
        return

    if os.path.isfile(路径):
        print(f"[调试] 截图已保存: {路径}")
    else:
        print(f"[调试] 写入后未找到文件，请检查路径权限: {路径}")

    if 显示窗口:
        cv2.imshow("aaa调试预览", 预览)
        print("[调试] 预览窗口已打开，按任意键关闭…")
        cv2.waitKey(0)
        cv2.destroyWindow("aaa调试预览")


def 获取当前视频帧(
    设备ID=None,
    scrcpy目录=None,
    *,
    max_size=None,
    video_bit_rate=16_000_000,
    调试=False,
    调试保存目录=None,
    调试显示窗口=False,
    调试保存格式="bmp",
):
    """
    取当前一帧（走 scrcpy 编码流，非 adb screencap）。

    每次调用会建立/拆除一次流，约 1～2 秒开销；循环取帧请用 设备视频流会话类 或::

        with Scrcpy视频流类(设备ID, scrcpy目录) as v:
            while True:
                bgr = v.读取一帧()

    :param 设备ID: adb devices 序列号，单设备可 None。
    :param scrcpy目录: 已忽略（兼容旧参数）；服务端由 scrcpy-core 自带。
    :param max_size: 长边上限制（如 1280）；默认 None 为原机分辨率，更清晰。
    :param video_bit_rate: H.264 码率；默认 16Mbps 减轻块糊，不需要可传 None。
    :param 调试: 为 True 时落盘并打印绝对路径（默认目录见 设置.缓存目录/aaa调试截图）。
    :param 调试保存目录: 覆盖默认调试保存目录。
    :param 调试显示窗口: 为 True 时用 OpenCV 弹窗显示本帧（会先保存文件）。
    :param 调试保存格式: \"bmp\"（默认，无压缩位图）或 \"png\"（无损 PNG）。
    :return: numpy.ndarray (BGR, 与 OpenCV 一致)；失败返回 None。
    """
    try:
        with Scrcpy视频流类(
            设备ID=设备ID,
            scrcpy目录=scrcpy目录 or _DEFAULT_SCRCPY_DIR,
            max_size=max_size,
            video_bit_rate=video_bit_rate,
        ) as v:
            帧 = v.读取一帧()
        if 帧 is not None and (调试 or 调试显示窗口):
            _调试输出截图(
                帧,
                前缀="视频帧",
                保存目录=调试保存目录,
                显示窗口=调试显示窗口,
                保存格式=调试保存格式,
            )
        return 帧
    except Exception as e:
        print(f"取视频帧失败: {e}")
        return None


def 视频帧转pil(bgr: np.ndarray):
    """BGR numpy -> PIL RGB。"""
    if bgr is None:
        return None
    rgb = bgr[:, :, ::-1]
    return Image.fromarray(rgb)



if __name__ == "__main__":
    # 示例：长会话多帧（请把设备 ID 改成你的）
    with 设备视频流会话类("9a8de478") as cam:
        while True:
            帧 = cam.获取当前视频帧()
            _调试输出截图(帧,前缀="视频帧")
            time.sleep(1) 
