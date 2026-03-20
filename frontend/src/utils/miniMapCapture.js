import { ipc, isEE } from "@/utils/ipcRenderer";
import { getMatchSocket } from "@/utils/matchSocket";
import { ipcApiRoute } from "@/api";

/**
 * 创建一个“小地图截屏帧”捕获器：
 * - 调用 start() 会打开小地图截屏悬浮框（Electron 内部已固定 1s 捕获一次）
 * - 监听 socket 的 `mini-map-frame`，把每帧 `image` dataUrl 交给回调
 * - 调用 stop() 会关闭悬浮框并解除监听
 */
export function createMiniMapFrameCapturer({
  size = 240,
  onFrame,
} = {}) {
  const capturer = {
    isRunning: false,
    latestMeta: null,
  };

  let socket = getMatchSocket() || window.matchSocket;
  if (!isEE && !socket) {
    // 纯浏览器环境下没有 ipc/socket，提前报错更友好
    // eslint-disable-next-line no-console
    console.warn("[miniMapCapture] Not in Electron / socket not ready");
  }

  const frameListener = (data = {}) => {
    if (!capturer.isRunning) return;
    const payload = data || {};
    const image = payload.image;
    if (typeof image === "string" && image) {
      if (typeof onFrame === "function") onFrame(payload);
    }
    // meta 字段可能也会在外部发来，这里先保留最新值
    capturer.latestMeta = payload;
  };

  const start = async () => {
    if (capturer.isRunning) return;
    socket = getMatchSocket() || window.matchSocket;
    if (!socket || typeof socket.on !== "function") {
      throw new Error("socket 未就绪：无法订阅 mini-map-frame");
    }
    if (!ipc || typeof ipc.invoke !== "function") {
      throw new Error("ipc 未就绪：无法打开小地图截屏框");
    }

    socket.on("mini-map-frame", frameListener);

    await ipc.invoke(ipcApiRoute.打开小地图截屏框, { size });
    capturer.isRunning = true;
  };

  const stop = async () => {
    if (!capturer.isRunning) return;
    if (socket && typeof socket.off === "function") {
      socket.off("mini-map-frame", frameListener);
    }
    capturer.isRunning = false;
    try {
      await ipc.invoke(ipcApiRoute.关闭小地图截屏框);
    } catch (e) {
      // 关闭失败不影响解除监听
    }
  };

  return {
    ...capturer,
    start,
    stop,
  };
}

