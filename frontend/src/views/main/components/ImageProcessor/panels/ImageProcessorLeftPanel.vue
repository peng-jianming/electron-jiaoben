<template>
  <div class="left-panel">
    <!-- 设备区域 -->
    <div class="panel-section">
      <div class="section-label">
        <span class="section-icon">📱</span>
        <span>设备连接</span>
      </div>
      <div class="device-status" :class="{ connected: isConnected }">
        <span class="device-dot"></span>
        <span class="device-text" :title="statusText">{{ statusText }}</span>
      </div>
      <div class="btn-row">
        <el-button size="small" @click="$emit('open-device-dialog')">连接</el-button>
        <el-button
          size="small"
          type="primary"
          :loading="deviceTab === 'capture-window' ? captureWindowLoading : screenshotLoading"
          :disabled="!canScreenshot"
          @click="$emit('capture-screenshot')"
        >截图</el-button>
      </div>
    </div>

    <!-- 图片操作区域 -->
    <div class="panel-section">
      <div class="section-label">
        <span class="section-icon">🖼️</span>
        <span>图片操作</span>
      </div>
      <el-button size="small" type="primary" @click="$emit('load-image')">载入图片</el-button>
      <div class="btn-row">
        <el-button size="small" :disabled="!hasImage" @click="$emit('save-image')">保存</el-button>
        <el-button size="small" :disabled="!hasImage || !selectionInfo" @click="$emit('crop-image')">裁剪</el-button>
      </div>
    </div>

    <!-- 选取操作区域 -->
    <div class="panel-section">
      <div class="section-label">
        <span class="section-icon">✂️</span>
        <span>选取工具</span>
      </div>
      <el-button
        size="small"
        :type="selectionEnabled ? 'warning' : 'primary'"
        @click="$emit('toggle-selection')"
      >{{ selectionEnabled ? "取消选取" : "选取 (Alt+D)" }}</el-button>
      <div class="coord-display">
        <div class="coord-grid">
          <span class="coord-key">X</span><span class="coord-val">{{ selectionInfo ? selectionInfo.x : 0 }}</span>
          <span class="coord-key">Y</span><span class="coord-val">{{ selectionInfo ? selectionInfo.y : 0 }}</span>
          <span class="coord-key">W</span><span class="coord-val">{{ selectionInfo ? selectionInfo.w : 0 }}</span>
          <span class="coord-key">H</span><span class="coord-val">{{ selectionInfo ? selectionInfo.h : 0 }}</span>
        </div>
        <el-button
          size="small"
          class="copy-coord-btn"
          :disabled="!selectionInfo"
          @click="$emit('copy-selection')"
        >复制坐标</el-button>
      </div>
    </div>

    <!-- 缩放操作区域 -->
    <div class="panel-section">
      <div class="section-label">
        <span class="section-icon">🔍</span>
        <span>视图</span>
      </div>
      <div class="btn-row">
        <el-button size="small" @click="$emit('fit-to-window')">自适应</el-button>
        <el-button size="small" @click="$emit('reset-zoom')">重置</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  currentDeviceId: {
    type: String,
    default: "",
  },
  deviceTab: {
    type: String,
    default: "mobile",
  },
  screenshotLoading: {
    type: Boolean,
    default: false,
  },
  captureWindowLoading: {
    type: Boolean,
    default: false,
  },
  selectionEnabled: {
    type: Boolean,
    default: false,
  },
  selectionInfo: {
    type: Object,
    default: null,
  },
  hasImage: {
    type: Boolean,
    default: false,
  },
});

const canScreenshot = computed(
  () =>
    (props.deviceTab === "mobile" && !!props.currentDeviceId) ||
    props.deviceTab === "capture-window"
);

// 设备状态文案：
// - 手机/窗口/虚拟机：显示对应 ID（由上游保证含义）
// - 截屏窗口：固定显示“截屏”
const statusText = computed(() => {
  if (props.deviceTab === "capture-window") {
    return "截屏";
  }
  if (!props.currentDeviceId) {
    return "未连接";
  }
  return props.currentDeviceId.slice(0, 14);
});

const isConnected = computed(() => {
  if (props.deviceTab === "capture-window") {
    return true;
  }
  return !!props.currentDeviceId;
});

defineEmits([
  "load-image",
  "open-device-dialog",
  "capture-screenshot",
  "toggle-selection",
  "fit-to-window",
  "reset-zoom",
  "save-image",
  "crop-image",
  "copy-selection",
]);
</script>

<style scoped>
.left-panel {
  display: flex;
  flex-direction: column;
  width: 160px;
  min-width: 160px;
  max-width: 160px;
  height: 882px;
  padding: 0;
  gap: 0;
  overflow: hidden;
  box-sizing: border-box;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.panel-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 10px;
  border-bottom: 1px solid #e2e8f0;
  transition: background 0.15s ease;
}

.panel-section:last-child {
  border-bottom: none;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 2px;
}

.section-icon {
  font-size: 11px;
  line-height: 1;
}

/* 设备状态指示 */
.device-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 11px;
  color: #94a3b8;
  transition: all 0.2s ease;
}

.device-status.connected {
  background: rgba(16, 185, 129, 0.06);
  border-color: rgba(16, 185, 129, 0.2);
  color: #059669;
}

.device-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #cbd5e1;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.device-status.connected .device-dot {
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
  animation: device-pulse 2s ease-in-out infinite;
}

@keyframes device-pulse {
  0%, 100% { box-shadow: 0 0 4px rgba(16, 185, 129, 0.4); }
  50% { box-shadow: 0 0 8px rgba(16, 185, 129, 0.6); }
}

.device-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
  font-weight: 500;
}

/* 坐标显示 */
.coord-display {
  padding: 6px 8px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 11px;
}

.coord-grid {
  display: grid;
  grid-template-columns: 14px 1fr 14px 1fr;
  gap: 3px 4px;
  align-items: center;
  margin-bottom: 4px;
}

.copy-coord-btn {
  width: 100%;
  font-size: 11px;
  height: 24px;
  padding: 0 8px;
}

.coord-key {
  color: #6366f1;
  font-weight: 700;
  text-align: right;
  font-size: 10px;
}

.coord-val {
  color: #334155;
  font-weight: 600;
  font-size: 11px;
}

/* 按钮行 */
.btn-row {
  display: flex;
  gap: 4px;
}

.btn-row .el-button {
  flex: 1;
}

.el-button + .el-button {
  margin-left: 0;
}

.el-button {
  width: 100%;
}

/* 按钮圆角统一 */
.panel-section :deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.15s ease;
}
</style>
