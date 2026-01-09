<template>
  <el-dialog
    v-model="innerVisible"
    title="设备连接"
    width="520px"
  >
    <el-tabs v-model="innerTab">
      <el-tab-pane label="手机" name="mobile">
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
          <el-empty description="未发现设备，请点击刷新" />
        </div>

        <div v-else class="device-list-wrapper">
          <el-radio-group v-model="innerSelectedDeviceId" class="device-list">
            <el-radio 
              v-for="id in deviceList" 
              :key="id" 
              :label="id"
            >
              {{ id }}
              <span 
                v-if="currentDeviceId === id" 
                class="device-tag"
              >
                当前
              </span>
            </el-radio>
          </el-radio-group>
        </div>

        <div class="device-footer">
          <span class="device-footer-text">
            当前连接设备：{{ currentDeviceId || '未连接' }}
          </span>
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

      <el-tab-pane label="电脑" name="pc">
        <div class="device-placeholder">
          电脑连接功能开发中...
        </div>
      </el-tab-pane>

      <el-tab-pane label="虚拟机" name="vm">
        <div class="device-placeholder">
          虚拟机连接功能开发中...
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
  'connect-selected-device'
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
.device-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.device-tip {
  font-size: 12px;
  color: var(--text-secondary);
}

.device-empty {
  padding: 24px 0;
}

.device-list-wrapper {
  max-height: 260px;
  overflow-y: auto;
  margin-top: 8px;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-tag {
  margin-left: 8px;
  padding: 2px 6px;
  font-size: 12px;
  border-radius: 8px;
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.device-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.device-footer-text {
  font-size: 13px;
  color: var(--text-secondary);
}

.device-placeholder {
  padding: 24px 0;
  text-align: center;
  color: var(--text-secondary);
}
</style>


