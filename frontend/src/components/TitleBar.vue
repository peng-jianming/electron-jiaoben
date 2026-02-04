<template>
  <div class="title-bar">
    <div
      class="title-bar-drag"
      @mousedown="onTitleBarMouseDown"
    >
      <span class="title-text">{{ title }}</span>
    </div>
    <div class="window-controls">
      <div class="control-btn minimize" @click="handleMinimize" title="最小化">
        -
      </div>
      <div class="control-btn close" @click="handleClose" title="关闭">
        ×
      </div>
    </div>
  </div>
</template>

<script setup>
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";

defineProps({
  title: {
    type: String,
    default: "设备管理系统",
  },
});

// 窗口控制
function handleMinimize() {
  ipc.invoke(ipcApiRoute.操作主窗口, { 操作方法: "minimize" });
}

function handleClose() {
  ipc.invoke(ipcApiRoute.操作主窗口, { 操作方法: "close" });
}

// 标题栏拖动窗口（主进程设置位置）
let dragStart = null;

async function onTitleBarMouseDown(e) {
  if (e.button !== 0) return;
  try {
    const pos = await ipc.invoke(ipcApiRoute.获取主窗口位置);
    if (pos && typeof pos.x === "number" && typeof pos.y === "number") {
      dragStart = {
        mouseX: e.screenX,
        mouseY: e.screenY,
        winX: pos.x,
        winY: pos.y,
      };
      window.addEventListener("mousemove", onDragMove);
      window.addEventListener("mouseup", onDragEnd);
    }
  } catch (err) {
    console.error("获取窗口位置失败", err);
  }
}

function onDragMove(e) {
  if (!dragStart) return;
  const dx = e.screenX - dragStart.mouseX;
  const dy = e.screenY - dragStart.mouseY;
  ipc.invoke(ipcApiRoute.设置主窗口位置, {
    x: dragStart.winX + dx,
    y: dragStart.winY + dy,
  });
}

function onDragEnd() {
  dragStart = null;
  window.removeEventListener("mousemove", onDragMove);
  window.removeEventListener("mouseup", onDragEnd);
}
</script>

<style scoped lang="less">
.title-bar {
  height: 40px;
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 100;
}

.title-bar-drag {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  user-select: none;
  cursor: move;
  min-width: 0;
}

.title-text {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  padding-left: 10px;
}

.window-controls {
  display: flex;
  flex-shrink: 0;
}

.control-btn {
  width: 40px;
  height: 40px;
  line-height: 40px;
  text-align: center;
  cursor: pointer;
  font-size: 18px;
  color: #606266;
  transition: all 0.2s;
}

.control-btn:hover {
  background-color: #ecf5ff;
  color: #409eff;
}

.control-btn.close:hover {
  background-color: #f56c6c;
  color: #ffffff;
}
</style>
