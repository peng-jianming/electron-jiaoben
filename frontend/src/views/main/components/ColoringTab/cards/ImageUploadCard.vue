<template>
  <section class="card upload-card">
    <div class="card-header">
      <div class="card-icon upload-icon">
        <el-icon><Upload /></el-icon>
      </div>
      <h2>图像加载</h2>
    </div>
    <div class="card-body">
      <!-- 设备连接（参考 ImageProcessorLeftPanel） -->
      <div class="device-section">
        <div class="section-label">
          <span class="section-icon">📱</span>
          <span>设备连接</span>
        </div>
        <div class="device-status" :class="{ connected: !!currentDeviceId }">
          <span class="device-dot"></span>
          <span class="device-text" :title="currentDeviceId || '未连接'">{{ currentDeviceId ? currentDeviceId.slice(0, 14) : "未连接" }}</span>
        </div>
        <div class="btn-row">
          <el-button size="small" @click="$emit('open-device-dialog')">连接</el-button>
          <el-button
            size="small"
            type="primary"
            :loading="screenshotLoading"
            :disabled="!currentDeviceId"
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
import { Upload, RefreshRight } from '@element-plus/icons-vue';

defineProps({
  imageFileName: String,
  originalImageUrl: String,
  currentDeviceId: { type: String, default: "" },
  screenshotLoading: { type: Boolean, default: false },
});

const emit = defineEmits(['image-select', 'open-device-dialog', 'capture-screenshot']);

function handleImageSelect(file) {
  emit('image-select', file);
}
</script>

<style scoped>
.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: var(--shadow-lg);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(51, 65, 85, 0.3);
  border-bottom: 1px solid var(--border-color);
}

.card-header h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  flex: 1;
}

.card-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.upload-icon {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  color: white;
}

.card-body {
  padding: 12px;
}

/* 设备连接区（与 ImageProcessorLeftPanel 风格一致） */
.device-section {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}
.section-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 6px;
}
.section-icon {
  font-size: 11px;
}
.device-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: rgba(51, 65, 85, 0.4);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  transition: all 0.2s ease;
}
.device-status.connected {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: var(--primary-light);
}
.device-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-secondary);
  flex-shrink: 0;
  opacity: 0.7;
}
.device-status.connected .device-dot {
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
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

.upload-card {
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(59, 130, 246, 0.05) 100%);
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  background: transparent;
  border: 2px dashed var(--border-color);
  border-radius: 10px;
  transition: all 0.3s ease;
  padding: 16px;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
}

.upload-content {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}

.upload-big-icon {
  font-size: 28px;
  color: var(--primary-light);
}

.primary-text {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0;
}

.uploaded-state {
  display: flex;
  align-items: center;
  gap: 12px;
}

.thumb-wrapper {
  width: 64px;
  height: 64px;
  min-width: 64px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  background: #0f172a;
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
  gap: 8px;
}

.file-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
