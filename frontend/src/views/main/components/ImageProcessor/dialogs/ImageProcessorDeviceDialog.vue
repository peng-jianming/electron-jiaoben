<template>
  <el-dialog
    v-model="innerVisible"
    title="设备连接"
    width="500px"
    class="device-dialog"
  >
    <el-tabs v-model="innerTab">
      <el-tab-pane label="📱 手机" name="mobile">
        <div class="device-toolbar">
          <el-button 
            size="small" 
            type="primary" 
            @click="$emit('refresh-devices')" 
            :loading="deviceLoading"
          >
            刷新设备
          </el-button>
          <span class="device-tip">请确保手机已通过 USB 或 WiFi 连接到 ADB</span>
        </div>

        <div v-if="!deviceLoading && deviceList.length === 0" class="device-empty">
          <el-empty description="未发现设备，请点击刷新" :image-size="60" />
        </div>

        <div v-else class="device-list-wrapper">
          <el-radio-group v-model="innerSelectedDeviceId" class="device-list">
            <el-radio 
              v-for="id in deviceList" 
              :key="id" 
              :label="id"
              class="device-radio-item"
            >
              <span class="device-id-text">{{ id }}</span>
              <span 
                v-if="currentDeviceId === id" 
                class="device-tag"
              >
                当前连接
              </span>
            </el-radio>
          </el-radio-group>
        </div>

        <div class="device-footer">
          <div class="device-footer-left">
            <span class="device-footer-dot" :class="{ active: !!currentDeviceId }"></span>
            <span class="device-footer-text">
              {{ currentDeviceId || '未连接设备' }}
            </span>
          </div>
          <el-button 
            type="primary" 
            size="small" 
            @click="$emit('connect-selected-device')" 
            :disabled="!innerSelectedDeviceId"
          >
            连接设备
          </el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane label="💻 窗口" name="pc">
        <div class="device-placeholder">
          <span class="placeholder-icon">🚧</span>
          <span>窗口连接功能开发中...</span>
        </div>
      </el-tab-pane>

      <el-tab-pane label="🖥️ 虚拟机" name="vm">
        <div class="device-placeholder">
          <span class="placeholder-icon">🚧</span>
          <span>虚拟机连接功能开发中...</span>
        </div>
      </el-tab-pane>

      <el-tab-pane label="🖼️ 截屏窗口" name="capture-window">
        <div class="capture-window-section">
          <p class="capture-window-hint">打开后可拖动、缩放截屏框，在外部点击「截图」即可截取框内区域。</p>
          <el-button type="primary" @click="$emit('open-capture-window')">
            打开截屏窗口
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  tab: {
    type: String,
    default: 'mobile'
  },
  deviceList: {
    type: Array,
    default: () => []
  },
  deviceLoading: {
    type: Boolean,
    default: false
  },
  selectedDeviceId: {
    type: String,
    default: ''
  },
  currentDeviceId: {
    type: String,
    default: ''
  }
});

const emits = defineEmits([
  'update:visible',
  'update:tab',
  'update:selected-device-id',
  'refresh-devices',
  'connect-selected-device',
  'open-capture-window'
]);

const innerVisible = computed({
  get: () => props.visible,
  set: (val) => emits('update:visible', val)
});

const innerTab = computed({
  get: () => props.tab,
  set: (val) => emits('update:tab', val)
});

const innerSelectedDeviceId = computed({
  get: () => props.selectedDeviceId,
  set: (val) => emits('update:selected-device-id', val)
});
</script>

<style scoped>
/* 弹窗圆角 */
.device-dialog :deep(.el-dialog) {
  border-radius: 12px;
}

.device-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #e2e8f0;
  padding: 16px 20px;
}

.device-dialog :deep(.el-dialog__title) {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.device-dialog :deep(.el-dialog__body) {
  padding: 16px 20px;
}

.device-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.device-tip {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

.device-empty {
  padding: 20px 0;
}

.device-list-wrapper {
  max-height: 240px;
  overflow-y: auto;
  margin-top: 8px;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.device-radio-item {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.device-radio-item:hover {
  border-color: #c7d2fe;
  background: #fafafe;
}

.device-id-text {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 12px;
  font-weight: 500;
}

.device-tag {
  margin-left: 8px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 10px;
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.15);
}

.device-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}

.device-footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-footer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.device-footer-dot.active {
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
}

.device-footer-text {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.device-placeholder {
  padding: 40px 0;
  text-align: center;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.placeholder-icon {
  font-size: 28px;
  opacity: 0.6;
}

.capture-window-section {
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.capture-window-hint {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  text-align: center;
  line-height: 1.5;
}
</style>


