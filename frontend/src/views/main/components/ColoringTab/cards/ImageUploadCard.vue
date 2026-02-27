<template>
  <section class="card upload-card">
    <div class="card-body">
      <!-- 设备连接（参考 ImageProcessorLeftPanel） -->
      <div class="device-section">
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

      <div v-if="originalImageUrl" class="uploaded-state">
        <div class="thumb-wrapper">
          <img :src="originalImageUrl" alt="已上传图片" class="thumb-image" />
        </div>
        <div class="upload-meta">
          <span class="file-name" :title="imageFileName">{{ imageFileName }}</span>
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleImageSelect"
            accept="image/*"
          >
            <el-button size="small" type="primary" :icon="RefreshRight">重新选择</el-button>
          </el-upload>
        </div>
      </div>
      <el-upload
        v-else
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleImageSelect"
        accept="image/*"
        drag
        class="upload-dragger"
      >
        <div class="upload-content">
          <el-icon class="upload-big-icon"><Upload /></el-icon>
          <p class="primary-text">拖拽或点击上传图片</p>
        </div>
      </el-upload>
    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { Upload, RefreshRight } from "@element-plus/icons-vue";

const props = defineProps({
  imageFileName: String,
  originalImageUrl: String,
  currentDeviceId: { type: String, default: "" },
  deviceTab: { type: String, default: "mobile" },
  screenshotLoading: { type: Boolean, default: false },
  captureWindowLoading: { type: Boolean, default: false },
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
    // 截屏模式下，只要选择了该 Tab，就认为“已准备好截屏”
    return true;
  }
  return !!props.currentDeviceId;
});

const emit = defineEmits([
  "image-select",
  "open-device-dialog",
  "capture-screenshot",
]);

function handleImageSelect(file) {
  emit('image-select', file);
}
</script>

<style scoped lang="less">
@primary: #6366f1;
@primary-light: #818cf8;
@success: #10b981;
@bg-card: #ffffff;
@text-primary: #1e293b;
@text-secondary: #64748b;
@text-muted: #94a3b8;
@border: #e2e8f0;
@shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);

.card {
  background: @bg-card;
  border-radius: 10px;
  border: 1px solid @border;
  overflow: hidden;
  box-shadow: @shadow-sm;
  transition: border-color 0.2s ease;
}

.card:hover {
  border-color: #cbd5e1;
}

.card-body {
  padding: 10px 12px;
}

.device-section {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid @border;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: @text-muted;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 6px;
}

.section-icon {
  font-size: 11px;
}

.device-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  background: #f8fafc;
  border: 1px solid @border;
  border-radius: 6px;
  font-size: 11px;
  color: @text-secondary;
  margin-bottom: 8px;
  transition: all 0.2s ease;
}

.device-status.connected {
  background: rgba(16, 185, 129, 0.06);
  border-color: rgba(16, 185, 129, 0.25);
  color: @success;
}

.device-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: @text-muted;
  flex-shrink: 0;
}

.device-status.connected .device-dot {
  background: @success;
  box-shadow: 0 0 5px rgba(16, 185, 129, 0.4);
}

.device-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
  font-weight: 500;
}

.btn-row {
  display: flex;
  gap: 6px;
}

.btn-row .el-button {
  flex: 1;
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  background: #fafbfc;
  border: 1.5px dashed #cbd5e1;
  border-radius: 8px;
  transition: all 0.2s ease;
  padding: 14px;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: @primary;
  background: rgba(99, 102, 241, 0.03);
}

.upload-content {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
}

.upload-big-icon {
  font-size: 24px;
  color: @primary-light;
}

.primary-text {
  font-size: 13px;
  color: @text-secondary;
  margin: 0;
}

.uploaded-state {
  display: flex;
  align-items: center;
  gap: 10px;
}

.thumb-wrapper {
  width: 56px;
  height: 56px;
  min-width: 56px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid @border;
  background: #f1f5f9;
}

.thumb-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.upload-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-name {
  font-size: 12px;
  color: @text-primary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}
</style>
