<template>
  <div class="title-bar">
    <div class="title-bar-drag" @mousedown="onTitleBarMouseDown">
      <div class="logo-section">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
        <span class="title-text">{{ title }}</span>
      </div>
    </div>
    <div class="window-controls">
      <div class="control-btn minimize" @click="handleMinimize" title="最小化">
        <svg viewBox="0 0 12 12" width="12" height="12">
          <rect fill="currentColor" y="5" width="12" height="2" rx="1"/>
        </svg>
      </div>
      <div class="control-btn close" @click="handleClose" title="关闭">
        <svg viewBox="0 0 12 12" width="12" height="12">
          <path fill="currentColor" d="M7.41 6l3.29-3.29a1 1 0 00-1.41-1.41L6 4.59 2.71 1.3A1 1 0 001.3 2.71L4.59 6 1.3 9.29a1 1 0 001.41 1.41L6 7.41l3.29 3.29a1 1 0 001.41-1.41L7.41 6z"/>
        </svg>
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
@title-bar-height: 40px;
@primary-color: #5b6af0;
@bg-color: #f8fafc;
@border-color: #e2e8f0;
@text-primary: #1e293b;
@text-secondary: #64748b;

.title-bar {
  height: @title-bar-height;
  background: @bg-color;
  border-bottom: 1px solid @border-color;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
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
  padding-left: 15px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 26px;
  height: 26px;
  background: linear-gradient(135deg, @primary-color 0%, #8b5cf6 100%);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(91, 106, 240, 0.3);
}

.title-text {
  font-size: 13px;
  font-weight: 600;
  color: @text-primary;
  letter-spacing: 0.3px;
}

.window-controls {
  display: flex;
  flex-shrink: 0;
  height: 100%;
  gap: 2px;
  padding-right: 8px;
}

.control-btn {
  width: 32px;
  height: 32px;
  margin: auto 0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: @text-secondary;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #e2e8f0;
    color: @text-primary;
  }
  
  &.close:hover {
    background-color: #fee2e2;
    color: #dc2626;
  }
}
</style>
