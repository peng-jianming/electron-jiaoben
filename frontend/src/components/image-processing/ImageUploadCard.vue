<template>
  <div class="upload-card">
    <div class="upload-header">图片上传 / 设备截图</div>
    <div
      class="upload-area"
      @dragover.prevent
      @drop.prevent="onDrop"
      @click="onClickSelect"
    >
      <input
        ref="fileInputRef"
        type="file"
        accept="image/*"
        class="file-input"
        @change="onFileChange"
      />
      <div class="upload-hint">
        <div>点击或拖拽图片到此处上传</div>
        <div class="upload-sub-hint">支持常见图片格式（JPG/PNG/WebP 等）</div>
      </div>
    </div>
    <div v-if="fileName" class="file-info">
      当前选择：{{ fileName }}
    </div>

    <div class="device-section">
      <div class="device-info">
        <span class="device-label">当前连接设备：</span>
        <span class="device-id">
          {{ imageProcessingStore.currentDeviceId || '未连接' }}
        </span>
      </div>
      <div class="device-actions">
        <button
          class="btn btn-secondary"
          type="button"
          @click.stop="openDeviceDialog"
          :disabled="!imageProcessingStore.isBackendReady"
        >
          连接设备
        </button>
        <button
          class="btn btn-primary"
          type="button"
          @click.stop="onClickScreenshot"
          :disabled="
            !imageProcessingStore.isBackendReady ||
            !imageProcessingStore.currentDeviceId
          "
        >
          截图
        </button>
      </div>
    </div>

    <div v-if="showDeviceDialog" class="dialog-mask" @click.self="closeDeviceDialog">
      <div class="dialog">
        <div class="dialog-header">
          <div class="dialog-title">选择设备</div>
          <button class="dialog-close" type="button" @click="closeDeviceDialog">
            ✕
          </button>
        </div>
        <div class="dialog-tabs">
          <div class="dialog-tab active">设备</div>
        </div>
        <div class="dialog-body">
          <div v-if="!deviceList.length" class="empty-tip">
            暂未检测到设备，请确认手机已连接并开启调试。
          </div>
          <ul v-else class="device-list">
            <li
              v-for="d in deviceList"
              :key="d"
              :class="[
                'device-item',
                d === selectedDeviceId ? 'active' : '',
              ]"
              @click="selectedDeviceId = d"
            >
              <span class="device-item-id">{{ d }}</span>
              <span
                v-if="d === imageProcessingStore.currentDeviceId"
                class="device-item-tag"
              >
                当前
              </span>
            </li>
          </ul>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-secondary" type="button" @click="closeDeviceDialog">
            取消
          </button>
          <button
            class="btn btn-primary"
            type="button"
            :disabled="!selectedDeviceId"
            @click="confirmConnect"
          >
            连接
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useImageProcessingStore } from '@/stores/imageProcessing';

const fileInputRef = ref(null);
const fileName = ref('');
const imageProcessingStore = useImageProcessingStore();

const showDeviceDialog = ref(false);
const selectedDeviceId = ref('');

const deviceList = computed(() => imageProcessingStore.adbDevices || []);

watch(
  () => imageProcessingStore.currentDeviceId,
  (val) => {
    if (val && !selectedDeviceId.value) {
      selectedDeviceId.value = val;
    }
  }
);

// 仅在前端本地生成预览，不再把 base64 发给后端
const readFileAsDataUrl = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });
};

const handleFile = async (file) => {
  if (!file) return;
  fileName.value = file.name;

  const filePath = file.path || '';
  let preview = '';

  try {
    // 预览仍然使用 dataUrl，但只在前端本地使用
    preview = await readFileAsDataUrl(file);
  } catch (e) {
    console.error('读取图片失败', e);
    preview = '';
  }

  // 直接交给全局 store 处理
  imageProcessingStore.handleImageChange({
    path: filePath,
    preview,
  });
};

const onFileChange = async (event) => {
  const files = event.target.files;
  if (!files || !files.length) return;
  await handleFile(files[0]);
  // 清空 input，方便再次选择同一张图片也能触发 change
  event.target.value = '';
};

const onDrop = async (event) => {
  const files = event.dataTransfer?.files;
  if (!files || !files.length) return;
  await handleFile(files[0]);
};

const onClickSelect = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
};

const openDeviceDialog = () => {
  imageProcessingStore.requestAdbDevices();
  showDeviceDialog.value = true;
  selectedDeviceId.value =
    imageProcessingStore.currentDeviceId ||
    (deviceList.value.length ? deviceList.value[0] : '');
};

const closeDeviceDialog = () => {
  showDeviceDialog.value = false;
};

const confirmConnect = () => {
  if (!selectedDeviceId.value) return;
  imageProcessingStore.connectAdbDevice(selectedDeviceId.value);
  showDeviceDialog.value = false;
};

const onClickScreenshot = () => {
  imageProcessingStore.takeAdbScreenshot();
};
</script>

<style scoped>
.upload-card {
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 12px;
  background-color: #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.upload-header {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.upload-area {
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  padding: 20px 12px;
  text-align: center;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.upload-area:hover {
  border-color: #3b82f6;
  background-color: #f1f5f9;
}

.upload-sub-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #9ca3af;
}

.file-input {
  display: none;
}

.file-info {
  margin-top: 8px;
  font-size: 12px;
  color: #4b5563;
}

.device-section {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px dashed #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.device-info {
  font-size: 12px;
  color: #4b5563;
  display: flex;
  align-items: center;
  gap: 4px;
}

.device-label {
  color: #6b7280;
}

.device-id {
  font-weight: 500;
}

.device-actions {
  display: flex;
  gap: 8px;
}

.btn {
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease,
    color 0.15s ease, opacity 0.15s ease;
}

.btn-primary {
  background-color: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

.btn-primary:hover:enabled {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-secondary {
  background-color: #f3f4f6;
  border-color: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover:enabled {
  background-color: #e5e7eb;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dialog-mask {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.dialog {
  width: 420px;
  max-width: calc(100% - 32px);
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 20px 35px rgba(15, 23, 42, 0.18);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  padding: 10px 14px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-title {
  font-size: 14px;
  font-weight: 600;
}

.dialog-close {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: #6b7280;
}

.dialog-tabs {
  display: flex;
  padding: 6px 10px 0;
}

.dialog-tab {
  font-size: 12px;
  padding: 4px 10px 6px;
  border-bottom: 2px solid transparent;
  color: #6b7280;
}

.dialog-tab.active {
  border-color: #2563eb;
  color: #2563eb;
  font-weight: 500;
}

.dialog-body {
  padding: 10px 14px 4px;
  max-height: 260px;
  overflow: auto;
}

.empty-tip {
  font-size: 12px;
  color: #9ca3af;
}

.device-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.device-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  color: #374151;
}

.device-item:hover {
  background-color: #f3f4f6;
}

.device-item.active {
  background-color: #eff6ff;
  color: #1d4ed8;
}

.device-item-id {
  word-break: break-all;
}

.device-item-tag {
  font-size: 11px;
  color: #2563eb;
}

.dialog-footer {
  padding: 8px 14px 10px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
