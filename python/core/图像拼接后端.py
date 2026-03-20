import base64
import json
import os
import re
import uuid
import traceback
from io import BytesIO
from urllib.parse import unquote, urlparse

import cv2
import numpy as np
from PIL import Image

from 设置 import 缓存图片目录, 图像处理参数配置路径
from core.图像处理后端 import 应用颜色过滤, 对图像应用膨胀, 对图像应用腐蚀


def _normalize_windows_path(raw_path: str) -> str:
    """
    兼容前端可能传来的多种路径格式：
    - C:\\Users\\xx\\a.png
    - file:///C:/Users/xx/a.png
    - /C:/Users/xx/a.png
    - /mnt/c/Users/xx/a.png
    """
    if not isinstance(raw_path, str):
        return ""
    p = raw_path.strip().strip("'").strip('"')
    if not p:
        return ""

    # file:// URI -> 普通路径
    if p.lower().startswith("file://"):
        parsed = urlparse(p)
        p = unquote(parsed.path or "")
        # 常见格式: /C:/Users/...
        if re.match(r"^/[a-zA-Z]:/", p):
            p = p[1:]

    # /mnt/c/Users/... -> C:\Users\...
    m = re.match(r"^/mnt/([a-zA-Z])/(.+)$", p)
    if m:
        drive = m.group(1).upper()
        rest = m.group(2).replace("/", "\\")
        p = f"{drive}:\\{rest}"

    # /C:/Users/... -> C:\Users\...
    if re.match(r"^/[a-zA-Z]:/", p):
        p = p[1:]

    # C:/Users/... -> C:\Users\...
    if re.match(r"^[a-zA-Z]:/", p):
        p = p.replace("/", "\\")

    return os.path.normpath(p)


def _resolve_existing_image_path(img_path: str) -> str:
    """
    尝试把输入路径归一化到当前运行环境可访问的真实路径。
    """
    candidates = []

    if isinstance(img_path, str):
        candidates.append(img_path)
        candidates.append(_normalize_windows_path(img_path))
        candidates.append(img_path.replace("/", "\\"))
        candidates.append(img_path.replace("\\", "/"))

    for c in candidates:
        if not c:
            continue
        try:
            if os.path.exists(c):
                return c
        except Exception:
            continue

    return ""


def _cv2_gray_or_bgr_to_dataurl(img: np.ndarray) -> str:
    """
    将 OpenCV 图像编码为 dataUrl（PNG）。
    img 可以是灰度(2维)或 BGR(3维)。
    """
    if img is None:
        raise ValueError("img is None")
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ValueError("PNG 编码失败")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return "data:image/png;base64," + b64


def _读取已保存的流水线参数():
    if not os.path.exists(图像处理参数配置路径):
        return []
    try:
        with open(图像处理参数配置路径, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    steps = data.get("steps") or []
    if not isinstance(steps, list):
        return []
    return steps


def _应用流水线(img, 步骤列表):
    """
    与图像处理后端保持一致的步骤处理逻辑。
    """
    out = img
    for step in 步骤列表:
        if not isinstance(step, dict):
            continue
        step_type = step.get("type")
        params = step.get("params") or {}

        if step_type == "二值化":
            threshold = params.get("threshold", 127)
            try:
                threshold = int(threshold)
            except Exception:
                threshold = 127
            gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY) if len(out.shape) == 3 else out
            _, out = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        elif step_type == "颜色过滤":
            list_rows = params.get("list") or []
            out = 应用颜色过滤(out, list_rows)
        elif step_type in ("膨胀", "腐蚀"):
            kernel_size = params.get("kernelSize", 3)
            iterations = params.get("iterations", 1)
            kernel_shape = params.get("kernelShape", "rect")

            try:
                kernel_size = int(kernel_size)
            except Exception:
                kernel_size = 3
            try:
                iterations = int(iterations)
            except Exception:
                iterations = 1

            if kernel_size < 1:
                kernel_size = 1
            if kernel_size % 2 == 0:
                kernel_size += 1
            if iterations < 1:
                iterations = 1

            if step_type == "膨胀":
                out = 对图像应用膨胀(
                    out, kernel_size=kernel_size, iterations=iterations, kernel_shape=kernel_shape
                )
            else:
                out = 对图像应用腐蚀(
                    out, kernel_size=kernel_size, iterations=iterations, kernel_shape=kernel_shape
                )
        else:
            # 拼接场景里忽略未知步骤，保证流程可执行
            continue
    return out


def load_binary_map(img_path: str, pipeline_steps):
    """
    读取图像并执行“图像处理流水线步骤”，最终转换为二值矩阵（0/1 uint8）。
    固定：白色为边界=1，黑色为可通行=0（阈值=127）。
    """
    if not img_path or not isinstance(img_path, str):
        raise ValueError("img_path 必须为字符串")
    resolved_path = _resolve_existing_image_path(img_path)
    if not resolved_path:
        raise FileNotFoundError(f"无法读取图像: {img_path}")

    # 参考图像处理后端：统一由 PIL 读取路径（对 Windows 中文路径更稳定）
    try:
        pil_img = Image.open(resolved_path).convert("RGB")
        img_rgb = np.array(pil_img, dtype=np.uint8)
        img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise FileNotFoundError(f"无法读取图像: {resolved_path}, error={e}")

    processed = _应用流水线(img, pipeline_steps or [])
    if processed is None:
        raise ValueError("流水线处理失败")

    # 最终统一成单通道
    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY) if len(processed.shape) == 3 else processed

    has_binary_step = any(isinstance(step, dict) and step.get("type") == "二值化" for step in (pipeline_steps or []))
    if has_binary_step:
        # 图像处理流水线中的二值化输出通常是 0/255，这里压缩为 0/1（白色为1）。
        binary = (gray > 0).astype(np.uint8)
    else:
        _, binary = cv2.threshold(gray, 127, 1, cv2.THRESH_BINARY)

    return binary.astype(np.uint8)


def _dataurl_to_bgr(img_data_url: str) -> np.ndarray:
    """
    将 dataUrl（PNG/JPEG 等）解码为 OpenCV BGR ndarray。
    """
    if not isinstance(img_data_url, str) or "," not in img_data_url:
        raise ValueError("无效的 dataUrl")
    _, b64 = img_data_url.split(",", 1)
    img_bytes = base64.b64decode(b64, validate=False)

    pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
    img_rgb = np.array(pil_img, dtype=np.uint8)
    return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)


def load_binary_map_from_dataurl(img_data_url: str, pipeline_steps, skip_pipeline_steps: bool = False):
    """
    读取 dataUrl 并转换为二值矩阵（0/1 uint8）。

    - skip_pipeline_steps=True：跳过“图像处理流水线步骤”，适用于 dataUrl 已被流水线处理过的场景。
    - skip_pipeline_steps=False：会先执行流水线步骤，再二值化。
    """
    if not img_data_url or not isinstance(img_data_url, str):
        raise ValueError("img_data_url 必须为字符串")

    img = _dataurl_to_bgr(img_data_url)
    processed = img
    if not skip_pipeline_steps:
        processed = _应用流水线(img, pipeline_steps or [])
        if processed is None:
            raise ValueError("流水线处理失败")

    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY) if len(processed.shape) == 3 else processed
    has_binary_step = any(isinstance(step, dict) and step.get("type") == "二值化" for step in (pipeline_steps or []))
    if has_binary_step:
        binary = (gray > 0).astype(np.uint8)
    else:
        _, binary = cv2.threshold(gray, 127, 1, cv2.THRESH_BINARY)

    return binary.astype(np.uint8)


def find_offset_by_correlation(img1: np.ndarray, img2: np.ndarray):
    """
    使用归一化互相关找到 img2 相对于 img1 的最佳平移偏移 (dx, dy)。
    返回 (dx, dy, confidence)
    """
    if img1 is None or img2 is None:
        raise ValueError("img1/img2 is None")
    if img1.ndim != 2 or img2.ndim != 2:
        raise ValueError("img1/img2 必须为 2D 二值矩阵")

    h1, w1 = img1.shape
    h2, w2 = img2.shape

    MAX_DX = 300
    MAX_DY = 200
    off_x = max(MAX_DX, abs(w2 - w1) // 2 + 2)
    off_y = max(MAX_DY, abs(h2 - h1) // 2 + 2)

    # 创建画布，将 img1 放在中央
    canvas_h = h1 + 2 * off_y
    canvas_w = w1 + 2 * off_x
    canvas = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    canvas[off_y : off_y + h1, off_x : off_x + w1] = img1.astype(np.float32)

    # 模板匹配（归一化互相关）
    result = cv2.matchTemplate(canvas, img2.astype(np.float32), cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    best_x, best_y = max_loc

    dx = best_x - off_x
    dy = best_y - off_y
    return int(dx), int(dy), float(max_val)


def _stitch_binary_by_offsets(binary_list, offsets):
    """
    binary_list: 每张图的 0/1 二值矩阵（uint8）
    offsets: 每张图在全局坐标系的 (x, y)（顶点坐标）
    """
    if not binary_list or not offsets or len(binary_list) != len(offsets):
        raise ValueError("binary_list/offsets 数量不一致")

    x_min = min(x for x, _y in offsets)
    y_min = min(y for _x, y in offsets)
    x_max = max(x + b.shape[1] for (x, _y), b in zip(offsets, binary_list))
    y_max = max(y + b.shape[0] for (x, y), b in zip(offsets, binary_list))

    canvas_w = max(1, x_max - x_min)
    canvas_h = max(1, y_max - y_min)
    canvas = np.zeros((canvas_h, canvas_w), dtype=np.uint8)

    for (x, y), b in zip(offsets, binary_list):
        x0 = x - x_min
        y0 = y - y_min
        h, w = b.shape[:2]
        # 边界保护（理论上不会越界，但防御式处理）
        if x0 < 0 or y0 < 0:
            continue
        if y0 + h > canvas_h or x0 + w > canvas_w:
            continue
        # 参考脚本：后图写入覆盖前图
        canvas[y0 : y0 + h, x0 : x0 + w] = b

    return canvas


class 图像拼接后端类:
    """
    图像拼接 tab 后端：
    - 输入：多张图片路径列表
    - 处理：
      1) 每张图按“图像处理流水线参数”处理
      2) 对处理后图做二值化矩阵化
      3) 链式互相关匹配（只匹配相邻帧，避免 O(N^2)）
      4) 将所有处理后的二值图按偏移拼接（union）
    - 输出：拼接后的预览图（限制输出尺寸，避免 base64 过大）
    """

    def __init__(self, 通信管理器):
        self._通信管理器 = 通信管理器
        # 增量拼接会话：用于“累计结果 + 新截图”的逐帧拼接
        # sessionId -> { canvas, x_min, y_min, last_bin, last_global_x, last_global_y, frame_count }
        self._incremental_sessions = {}

    def _ensure_dir(self, dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception:
            pass

    def _发送进度(self, request_id: str, progress: int, stage: str, message: str):
        try:
            self._通信管理器.发送到Electron(
                "image-stitching-progress",
                {
                    "requestId": request_id,
                    "progress": min(100, max(0, int(progress))),
                    "stage": stage,
                    "message": message,
                },
            )
        except Exception:
            pass

    def _处理非增量拼接(self, inputs, request_id: str, loader_fn):
        """
        通用的“链式互相关匹配 + 拼接画布生成”逻辑。
        通过 loader_fn 决定 inputs 是“路径”还是“截屏 dataUrl”。
        """
        total = len(inputs)
        bin_list = []
        offsets = [(0, 0)]
        global_x = 0
        global_y = 0
        prev_bin = None

        b0 = loader_fn(inputs[0])
        bin_list.append(b0)
        prev_bin = b0

        for idx in range(1, total):
            b = loader_fn(inputs[idx])
            bin_list.append(b)

            dx, dy, conf = find_offset_by_correlation(prev_bin, b)
            print(f"匹配偏移: dx={dx}, dy={dy}, conf={conf:.4f}")
            global_x += dx
            global_y += dy
            offsets.append((global_x, global_y))

            prev_bin = b

            progress = int(((idx + 1) / total) * 70)
            self._发送进度(
                request_id,
                progress=progress,
                stage="matching",
                message=f"匹配中：{idx + 1}/{total} (conf={conf:.3f})",
            )

        canvas = _stitch_binary_by_offsets(bin_list, offsets)
        self._发送进度(request_id, progress=80, stage="stitching", message="开始拼接…")

        vis = (canvas * 255).astype(np.uint8)
        dataurl = _cv2_gray_or_bgr_to_dataurl(vis)

        # 同时保存一份到磁盘，便于调试与复查
        try:
            out_dir = os.path.join(缓存图片目录, "image-stitching")
            self._ensure_dir(out_dir)
            out_full_path = os.path.join(out_dir, f"{request_id}.png")
            cv2.imwrite(out_full_path, (canvas * 255).astype(np.uint8))
        except Exception:
            pass

        self._通信管理器.发送到Electron(
            "image-stitching-result",
            {"requestId": request_id, "image": dataurl},
        )

    def _处理非增量拼接_上传图片(self, image_paths, request_id: str, pipeline_steps):
        def loader_fn(p):
            return load_binary_map(p, pipeline_steps=pipeline_steps)

        return self._处理非增量拼接(image_paths, request_id, loader_fn=loader_fn)

    def _处理非增量拼接_截屏dataUrl(self, image_data_urls, request_id: str, pipeline_steps, skip_pipeline_steps: bool):
        def loader_fn(d):
            return load_binary_map_from_dataurl(
                d,
                pipeline_steps=pipeline_steps,
                skip_pipeline_steps=skip_pipeline_steps,
            )

        return self._处理非增量拼接(image_data_urls, request_id, loader_fn=loader_fn)

    def _处理增量拼接_截屏dataUrl(
        self,
        request_id: str,
        session_id: str,
        incremental_operation: str,
        image_data_urls,
        pipeline_steps,
        skip_pipeline_steps: bool,
    ):
        if str(incremental_operation) == "end":
            if session_id in self._incremental_sessions:
                del self._incremental_sessions[session_id]
            return

        if not isinstance(image_data_urls, list) or len(image_data_urls) < 1:
            raise ValueError("增量拼接需要至少 1 帧 dataUrl")

        img_item = image_data_urls[0]
        b_new = load_binary_map_from_dataurl(
            img_item,
            pipeline_steps=pipeline_steps,
            skip_pipeline_steps=skip_pipeline_steps,
        )

        if str(incremental_operation) == "init":
            self._incremental_sessions[session_id] = {
                "canvas": b_new.astype(np.uint8),
                "x_min": 0,
                "y_min": 0,
                "last_bin": b_new.astype(np.uint8),
                "last_global_x": 0,
                "last_global_y": 0,
                "frame_count": 1,
            }
        elif str(incremental_operation) == "step":
            sess = self._incremental_sessions.get(session_id)
            if not sess:
                raise ValueError(f"增量会话不存在: sessionId={session_id}")

            canvas = sess["canvas"]
            x_min = int(sess["x_min"])
            y_min = int(sess["y_min"])
            last_bin = sess["last_bin"]
            last_global_x = int(sess["last_global_x"])
            last_global_y = int(sess["last_global_y"])

            dx, dy, _conf = find_offset_by_correlation(last_bin, b_new)
            new_global_x = last_global_x + dx
            new_global_y = last_global_y + dy

            # 扩展 canvas 以容纳新帧
            canvas_h, canvas_w = canvas.shape[:2]
            frame_h, frame_w = b_new.shape[:2]

            desired_x_min = min(x_min, new_global_x)
            desired_y_min = min(y_min, new_global_y)
            desired_x_max = max(x_min + canvas_w, new_global_x + frame_w)
            desired_y_max = max(y_min + canvas_h, new_global_y + frame_h)

            if (
                desired_x_min != x_min
                or desired_y_min != y_min
                or desired_x_max != x_min + canvas_w
                or desired_y_max != y_min + canvas_h
            ):
                new_canvas_w = max(1, int(desired_x_max - desired_x_min))
                new_canvas_h = max(1, int(desired_y_max - desired_y_min))
                new_canvas = np.zeros((new_canvas_h, new_canvas_w), dtype=np.uint8)
                x_shift = x_min - desired_x_min
                y_shift = y_min - desired_y_min
                new_canvas[y_shift : y_shift + canvas_h, x_shift : x_shift + canvas_w] = canvas
                canvas = new_canvas
                x_min = int(desired_x_min)
                y_min = int(desired_y_min)

            x0 = new_global_x - x_min
            y0 = new_global_y - y_min

            # 写入/覆盖：后图覆盖前图
            canvas[y0 : y0 + frame_h, x0 : x0 + frame_w] = b_new

            # 更新会话状态
            sess["canvas"] = canvas
            sess["x_min"] = x_min
            sess["y_min"] = y_min
            sess["last_bin"] = b_new
            sess["last_global_x"] = new_global_x
            sess["last_global_y"] = new_global_y
            sess["frame_count"] = int(sess.get("frame_count") or 0) + 1
        else:
            raise ValueError(f"未知增量操作: {incremental_operation}")

        canvas_out = self._incremental_sessions[session_id]["canvas"]
        vis = (canvas_out * 255).astype(np.uint8)
        dataurl = _cv2_gray_or_bgr_to_dataurl(vis)
        self._通信管理器.发送到Electron(
            "image-stitching-result",
            {"requestId": request_id, "image": dataurl},
        )

    def 处理图像拼接(self, 数据):
        """
        类型：图像拼接
        参数：
        - 图片路径列表: List[str]
        - requestId: str
        """
        try:
            payload = 数据 or {}
            print(数据, "===")
            request_id = payload.get("requestId") or payload.get("request_id") or uuid.uuid4().hex

            image_paths = payload.get("图片路径列表") or payload.get("imagePaths") or payload.get("image_paths") or []
            image_data_urls = (
                payload.get("图片dataUrl列表")
                or payload.get("imageDataUrls")
                or payload.get("dataUrl列表")
                or payload.get("data_urls")
                or []
            )

            inputs = []
            use_data_urls = False

            if isinstance(image_data_urls, list):
                inputs = [d for d in image_data_urls if isinstance(d, str) and d.startswith("data:")]
                # 增量拼接 init/step 只需要 1 帧，因此 dataUrl 只要 >=1 就算可用
                use_data_urls = len(inputs) >= 1

            if not use_data_urls:
                if not isinstance(image_paths, list):
                    raise ValueError("至少需要提供图片路径列表或 dataUrl 列表")
                inputs = [p for p in image_paths if isinstance(p, str) and p]

            模式 = payload.get("模式") or payload.get("mode") or payload.get("stitchMode") or ""
            session_id = payload.get("sessionId") or payload.get("stitchSessionId") or payload.get("拼接会话id") or ""
            增量操作 = payload.get("增量操作") or payload.get("incrementalOperation") or payload.get("operation") or ""

            skip_pipeline_steps = bool(payload.get("跳过流水线") or payload.get("skipPipeline") or False)

            is_incremental = str(模式) == "incremental" and isinstance(session_id, str) and session_id

            # 增量模式：init/step 需要 >=1 帧，end 不需要
            if is_incremental:
                if str(增量操作) != "end" and (not isinstance(inputs, list) or len(inputs) < 1):
                    raise ValueError("增量拼接需要至少 1 帧 dataUrl")
            else:
                if not isinstance(inputs, list) or len(inputs) < 2:
                    raise ValueError("至少需要 2 张图片进行拼接")

            pipeline_steps = _读取已保存的流水线参数()

            # ===== 输入来源分发：上传路径 vs 截屏 dataUrl =====
            # 目标：不要让“截屏”和“上传”复用同一个处理分支函数。
            if is_incremental:
                return self._处理增量拼接_截屏dataUrl(
                    request_id=request_id,
                    session_id=session_id,
                    incremental_operation=增量操作,
                    image_data_urls=inputs,
                    pipeline_steps=pipeline_steps,
                    skip_pipeline_steps=skip_pipeline_steps,
                )

            if use_data_urls:
                return self._处理非增量拼接_截屏dataUrl(
                    image_data_urls=inputs,
                    request_id=request_id,
                    pipeline_steps=pipeline_steps,
                    skip_pipeline_steps=skip_pipeline_steps,
                )

            return self._处理非增量拼接_上传图片(
                image_paths=inputs,
                request_id=request_id,
                pipeline_steps=pipeline_steps,
            )
        except Exception as e:
            print(f"图像拼接异常: {e}")
            traceback.print_exc()
            try:
                self._通信管理器.发送到Electron(
                    "image-stitching-error",
                    {"message": str(e), "requestId": (数据 or {}).get("requestId") or None},
                )
            except Exception:
                pass

