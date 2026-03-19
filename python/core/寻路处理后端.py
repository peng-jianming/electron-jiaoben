import base64
import os
import traceback
import uuid
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

from 设置 import 寻路缓存图片目录
from .图像处理后端 import 图像处理后端类


class Node:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)
        self.g = 0
        self.h = 0
        self.parent = None

    def f(self):
        return self.g + self.h

    def __lt__(self, other):
        return self.f() < other.f()


def bresenham_line(p1, p2):
    x1, y1 = int(p1[0]), int(p1[1])
    x2, y2 = int(p2[0]), int(p2[1])
    points = []

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        points.append((x1, y1))
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

    return points


def 补充直线(path_list):
    if not path_list:
        return []
    if len(path_list) == 1:
        return [tuple(path_list[0])]

    new_path_list = []
    for idx in range(len(path_list) - 1):
        p1 = path_list[idx]
        p2 = path_list[idx + 1]
        pts = bresenham_line(p1, p2)
        if new_path_list and pts:
            # 避免重复拼接的端点
            if new_path_list[-1] == pts[0]:
                pts = pts[1:]
        new_path_list.extend(pts)
    return new_path_list


class A_START:
    def __init__(self):
        self.deltas = [
            (0, 1, 10),
            (0, -1, 10),
            (1, 0, 10),
            (-1, 0, 10),
            (-1, -1, 14),
            (-1, 1, 14),
            (1, -1, 14),
            (1, 1, 14),
        ]

    def a_star(self, matrix, _start, _target, rows=(), cols=()):
        import heapq

        if matrix is None:
            return None
        h, w = matrix.shape[:2]
        if h <= 0 or w <= 0:
            return None

        start = Node(*_start)
        target = Node(*_target)

        min_rows, min_cols = rows if rows else (0, 0)
        max_rows, max_cols = h, w

        def in_range(nx, ny):
            return min_rows <= ny < max_rows and min_cols <= nx < max_cols

        # 0/255 或 0/1 都支持：非 0 视为可走
        def walkable(nx, ny):
            return bool(matrix[ny, nx])

        open_set = []
        heapq.heappush(open_set, (start.f(), start))
        close_list = np.zeros((h, w), dtype=bool)
        close_list[start.y, start.x] = True

        while open_set:
            _, current = heapq.heappop(open_set)
            if current.x == target.x and current.y == target.y:
                return self.reconstruct_path(current)

            for dx, dy, cost in self.deltas:
                nx = current.x + dx
                ny = current.y + dy
                if not in_range(nx, ny):
                    continue
                if close_list[ny, nx]:
                    continue
                if not walkable(nx, ny):
                    continue

                neighbor = Node(nx, ny)
                neighbor.g = current.g + cost
                neighbor.h = self.manhattan_distance(neighbor, target)
                neighbor.parent = current
                heapq.heappush(open_set, (neighbor.f(), neighbor))
                close_list[ny, nx] = True

        return None

    @staticmethod
    def manhattan_distance(node, target):
        x, y = abs(node.x - target.x), abs(node.y - target.y)
        if x <= y:
            return 14 * x + abs(x - y) * 10
        return 14 * y + abs(x - y) * 10

    @staticmethod
    def reconstruct_path(node):
        path = []
        while node.parent is not None:
            path.append((node.x, node.y))
            node = node.parent
        return list(reversed(path))


def _ensure_dir(dir_path):
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception:
        pass


def _to_gray_binary(img_bgr):
    if img_bgr is None:
        return None
    if len(img_bgr.shape) == 3:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_bgr
    _, th = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # 自动判断是否需要反色：白色过多时认为背景为白，翻转为“路=白”
    ratio = float(np.count_nonzero(th)) / float(th.size)
    if ratio > 0.6:
        th = cv2.bitwise_not(th)
    return th


def _zs_thinning(binary_255):
    """
    Zhang-Suen 细化，输入 0/255 二值，输出 0/255 骨架。
    """
    if binary_255 is None:
        return None
    img = (binary_255 > 0).astype(np.uint8)
    changed = True
    h, w = img.shape[:2]
    if h < 3 or w < 3:
        return (img * 255).astype(np.uint8)

    def neighbors(x, y):
        p2 = img[y - 1, x]
        p3 = img[y - 1, x + 1]
        p4 = img[y, x + 1]
        p5 = img[y + 1, x + 1]
        p6 = img[y + 1, x]
        p7 = img[y + 1, x - 1]
        p8 = img[y, x - 1]
        p9 = img[y - 1, x - 1]
        return [p2, p3, p4, p5, p6, p7, p8, p9]

    def transitions(ns):
        s = 0
        for i in range(len(ns)):
            if ns[i] == 0 and ns[(i + 1) % len(ns)] == 1:
                s += 1
        return s

    while changed:
        changed = False
        to_del = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if img[y, x] != 1:
                    continue
                ns = neighbors(x, y)
                n = sum(ns)
                if n < 2 or n > 6:
                    continue
                if transitions(ns) != 1:
                    continue
                if ns[0] * ns[2] * ns[4] != 0:
                    continue
                if ns[2] * ns[4] * ns[6] != 0:
                    continue
                to_del.append((x, y))
        if to_del:
            for x, y in to_del:
                img[y, x] = 0
            changed = True

        to_del = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if img[y, x] != 1:
                    continue
                ns = neighbors(x, y)
                n = sum(ns)
                if n < 2 or n > 6:
                    continue
                if transitions(ns) != 1:
                    continue
                if ns[0] * ns[2] * ns[6] != 0:
                    continue
                if ns[0] * ns[4] * ns[6] != 0:
                    continue
                to_del.append((x, y))
        if to_del:
            for x, y in to_del:
                img[y, x] = 0
            changed = True

    return (img * 255).astype(np.uint8)


def _thinning(binary_255):
    # 优先用 OpenCV ximgproc（若环境存在）
    try:
        thinning = cv2.ximgproc.thinning  # type: ignore
        return thinning(binary_255)
    except Exception:
        return _zs_thinning(binary_255)


def _find_nearest_white_point(thinned_255, loc_xy):
    if thinned_255 is None:
        return [-1, -1]
    h, w = thinned_255.shape[:2]
    x, y = int(loc_xy[0]), int(loc_xy[1])
    x = max(0, min(w - 1, x))
    y = max(0, min(h - 1, y))

    if thinned_255[y, x] == 255:
        return [x, y]

    tmp = thinned_255.copy()
    tmp[y, x] = 0
    white_points = np.argwhere(tmp == 255)
    if white_points.size == 0:
        return [-1, -1]
    white_xy = white_points[:, [1, 0]].astype(np.int32)
    target = np.array([x, y], dtype=np.int32)
    delta = white_xy - target
    sq = np.sum(delta ** 2, axis=1)
    idx = int(np.argmin(sq))
    loc2 = list(white_xy[idx])
    return [int(loc2[0]), int(loc2[1])]


def _draw_path_on_image(img_bgr, path_xy, color=(0, 0, 255), thickness=1):
    if img_bgr is None:
        return None
    if not path_xy:
        return img_bgr
    out = img_bgr.copy()
    # 逐点画，避免 polyline 对重复点/断点的奇怪表现
    for x, y in path_xy:
        cv2.circle(out, (int(x), int(y)), radius=max(1, thickness), color=color, thickness=-1)
    return out


class 寻路处理后端类:
    def __init__(self, 通信管理器, 图像处理后端实例: 图像处理后端类):
        self._通信管理器 = 通信管理器
        self._图像处理后端 = 图像处理后端实例
        # 记录当前用于寻路/匹配的原始地图 imageId
        self._current_image_id = None

    def _cv2_to_dataurl(self, img):
        return self._图像处理后端._cv2_to_dataurl(img)

    def _save_image_bytes(self, img_bytes):
        _ensure_dir(寻路缓存图片目录)
        image_id = uuid.uuid4().hex
        file_path = os.path.join(寻路缓存图片目录, f"{image_id}.png")
        pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
        pil_img.save(file_path, format="PNG")
        return image_id

    def _load_image_by_id(self, image_id, image_source="path"):
        if not image_id:
            raise ValueError("缺少 image_id")

        if image_source == "processing":
            return self._图像处理后端._load_image_by_id(image_id)

        if image_source == "flood":
            # 洪水填充缓存目录由洪水填充后端管理；这里不直接耦合其目录，前端如果要用洪水填充结果，
            # 会通过 寻路上传base64缓存 生成寻路专用 imageId
            pass

        _ensure_dir(寻路缓存图片目录)
        file_path = os.path.join(寻路缓存图片目录, f"{image_id}.png")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"寻路缓存图片不存在: image_id={image_id} path={file_path}")

        pil_img = Image.open(file_path).convert("RGB")
        img_rgb = np.array(pil_img)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        return img_bgr

    # ===== 对前端暴露：上传 =====
    def 处理上传图片(self, 数据):
        """
        - 类型：寻路上传缓存
        - 参数：{ 图片路径, requestId? }
        - 返回事件：path-image-uploaded { imageId, preview, requestId? }
        """
        try:
            payload = 数据 or {}
            图片路径 = payload.get("图片路径")
            request_id = payload.get("requestId")
            if not 图片路径 or not isinstance(图片路径, str):
                raise ValueError("未收到有效的图片路径")
            if not os.path.exists(图片路径):
                raise FileNotFoundError(f"图片路径不存在: {图片路径}")

            pil_img = Image.open(图片路径).convert("RGB")
            buf = BytesIO()
            pil_img.save(buf, format="PNG")
            image_id = self._save_image_bytes(buf.getvalue())
            # 记录当前原始地图 id，供后续匹配使用
            self._current_image_id = image_id

            img_rgb = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            preview_dataurl = self._cv2_to_dataurl(img_bgr)

            self._通信管理器.发送到Electron(
                "path-image-uploaded",
                {"imageId": image_id, "preview": preview_dataurl, "requestId": request_id},
            )
        except Exception as e:
            print(f"处理寻路上传图片异常: {e}")
            traceback.print_exc()

    def 处理上传base64图片(self, 数据):
        """
        - 类型：寻路上传base64缓存
        - 参数：{ dataUrl, requestId? }
        - 返回事件：path-image-uploaded { imageId, preview, requestId? }
        """
        try:
            payload = 数据 or {}
            data_url = payload.get("dataUrl") or payload.get("data_url") or ""
            request_id = payload.get("requestId")
            if not data_url or not isinstance(data_url, str):
                raise ValueError("未收到有效的 dataUrl")

            if "," in data_url:
                _, b64 = data_url.split(",", 1)
            else:
                b64 = data_url
            img_bytes = base64.b64decode(b64, validate=False)
            image_id = self._save_image_bytes(img_bytes)
            img_bgr = self._load_image_by_id(image_id)
            preview_dataurl = self._cv2_to_dataurl(img_bgr)

            # 记录当前原始地图 id，供后续匹配使用
            self._current_image_id = image_id

            self._通信管理器.发送到Electron(
                "path-image-uploaded",
                {"imageId": image_id, "preview": preview_dataurl, "requestId": request_id},
            )
        except Exception as e:
            print(f"处理寻路上传base64图片异常: {e}")
            traceback.print_exc()

    # ===== 对前端暴露：骨干网 =====
    def 处理获取骨干网(self, 数据):
        """
        - 类型：获取骨干网
        - 参数：{ imageId, imageSource? }
        - 返回事件：skeleton-result { image: dataUrl }
        """
        try:
            payload = 数据 or {}
            image_id = payload.get("imageId")
            image_source = payload.get("imageSource") or payload.get("image_source") or "path"
            if not image_id:
                raise ValueError("获取骨干网缺少 imageId")

            img = self._load_image_by_id(image_id, image_source=image_source)
            binary = _to_gray_binary(img)
            thinned = _thinning(binary)
            # 返回可视化：白骨架+黑背景
            dataurl = self._cv2_to_dataurl(thinned)
            self._通信管理器.发送到Electron("skeleton-result", {"image": dataurl})
        except Exception as e:
            print(f"获取骨干网异常: {e}")
            traceback.print_exc()
            try:
                self._通信管理器.发送到Electron("path-finding-error", {"message": str(e)})
            except Exception:
                pass

    # ===== 对前端暴露：寻路 =====
    def 处理寻路(self, 数据):
        """
        - 类型：寻路计算
        - 参数：{ imageId, imageSource?, start:{x,y}, end:{x,y} }
        - 返回事件：path-finding-result { image: dataUrl, path: [ [x,y], ... ] }
        """
        try:
            payload = 数据 or {}
            image_id = payload.get("imageId")
            image_source = payload.get("imageSource") or payload.get("image_source") or "path"
            start = payload.get("start") or {}
            end = payload.get("end") or {}
            sx = start.get("x")
            sy = start.get("y")
            ex = end.get("x")
            ey = end.get("y")

            if not image_id:
                raise ValueError("寻路计算缺少 imageId")
            if sx is None or sy is None or ex is None or ey is None:
                raise ValueError("寻路计算缺少起点或终点")

            img = self._load_image_by_id(image_id, image_source=image_source)
            binary = _to_gray_binary(img)
            thinned = _thinning(binary)

            start_loc = [int(sx), int(sy)]
            end_loc = [int(ex), int(ey)]
            start_loc2 = _find_nearest_white_point(thinned, start_loc)
            end_loc2 = _find_nearest_white_point(thinned, end_loc)
            if start_loc2[0] < 0 or end_loc2[0] < 0:
                raise ValueError("骨干网为空或无法找到最近骨干点")

            ax = A_START()
            result1 = 补充直线([start_loc, start_loc2])
            result2 = ax.a_star(thinned, start_loc2, end_loc2) or []
            result3 = 补充直线([end_loc2, end_loc])
            path = []
            for seg in (result1, result2, result3):
                for p in seg:
                    if not path or path[-1] != p:
                        path.append(p)

            # 画出骨干网(绿)+路径(红)
            vis = img.copy()
            ys, xs = np.where(thinned == 255)
            if xs.size > 0:
                vis[ys, xs] = (0, 255, 0)
            vis = _draw_path_on_image(vis, path, color=(0, 0, 255), thickness=1)
            cv2.circle(vis, (int(sx), int(sy)), 3, (255, 0, 0), -1)
            cv2.circle(vis, (int(ex), int(ey)), 3, (0, 255, 255), -1)

            dataurl = self._cv2_to_dataurl(vis)
            self._通信管理器.发送到Electron(
                "path-finding-result",
                {
                    "image": dataurl,
                    "path": [[int(x), int(y)] for (x, y) in path],
                    "startOnSkeleton": start_loc2,
                    "endOnSkeleton": end_loc2,
                },
            )
        except Exception as e:
            print(f"寻路计算异常: {e}")
            traceback.print_exc()
            try:
                self._通信管理器.发送到Electron("path-finding-error", {"message": str(e)})
            except Exception:
                pass

    # ===== 对前端 / 小地图处理暴露：原始地图模板匹配 =====
    def 处理小地图匹配(self, 数据):
        """
        小地图与原始地图进行模板匹配：
        - 被动从 socket 收到小地图帧（同 图像处理小地图 的数据结构）：{ dataUrl | image }
        - 使用当前记录的原始地图 imageId 作为大图，在其上用小地图做模板匹配
        - 返回事件：match-map-frame { image: dataUrl, score: float, topLeft: [x,y], center: [x,y], size: [w,h] }
        """
        try:
            if not self._current_image_id:
                return
            payload = 数据 or {}
            data_url = (
                payload.get("dataUrl")
                or payload.get("data_url")
                or payload.get("image")
                or ""
            )
            if not data_url or not isinstance(data_url, str):
                return
            # 解析 dataUrl 为 OpenCV BGR 图像
            try:
                if "," in data_url:
                    _, b64 = data_url.split(",", 1)
                else:
                    b64 = data_url
                img_bytes = base64.b64decode(b64, validate=False)
                pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
                mini_rgb = np.array(pil_img)
                mini_bgr = cv2.cvtColor(mini_rgb, cv2.COLOR_RGB2BGR)
            except Exception:
                return
            big_bgr = self._load_image_by_id(self._current_image_id, image_source="path")
            if big_bgr is None or mini_bgr is None:
                return
            big_h, big_w = big_bgr.shape[:2]
            mini_h, mini_w = mini_bgr.shape[:2]
            if big_h <= 0 or big_w <= 0 or mini_h <= 0 or mini_w <= 0:
                return
            if mini_h > big_h or mini_w > big_w:
                return
            big_gray = cv2.cvtColor(big_bgr, cv2.COLOR_BGR2GRAY)
            mini_gray = cv2.cvtColor(mini_bgr, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(big_gray, mini_gray, cv2.TM_CCOEFF_NORMED)
            _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(res)
            # 相似度过低则忽略
            if max_val < 0.3:
                return

            top_left = max_loc
            bottom_right = (top_left[0] + mini_w, top_left[1] + mini_h)
            center = (top_left[0] + mini_w // 2, top_left[1] + mini_h // 2)

            vis = big_bgr.copy()
            cv2.rectangle(vis, top_left, bottom_right, (0, 0, 255), 2)
            cv2.circle(vis, center, 4, (0, 255, 255), -1)

            dataurl = self._cv2_to_dataurl(vis)
            self._通信管理器.发送到Electron(
                "match-map-frame",
                {
                    "image": dataurl,
                    "score": float(max_val),
                    "topLeft": [int(top_left[0]), int(top_left[1])],
                    "center": [int(center[0]), int(center[1])],
                    "size": [int(mini_w), int(mini_h)],
                },
            )
        except Exception as e:
            print(f"小地图模板匹配异常: {e}")
            traceback.print_exc()




# 原始地图 + 截屏小地图 -> 得到当前小地图在原始地图的位置 -> 这个位置也是在规划图的位置 -> 也就是得到寻路的起始点坐标

# 规划图(得到骨干图)  + 终点(固定位置 -> 固定的寻路坐标列表

#  起始点(当前小地图位置) + 固定的寻路坐标列表 -> 循环获取固定的寻路坐标列表往终点方向可走的最远的直线的坐标点, 根据二点之间的方位,进行屏幕点击(角色屏幕中心点+半径范围)



