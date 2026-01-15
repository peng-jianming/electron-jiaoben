<template>
  <div class="left-panel">
    <div class="card">
      <div class="card-body">
        <el-button
          type="primary"
          :icon="Upload"
          @click="$emit('load-image')"
          class="action-btn"
        >
          载入图片
        </el-button>

        <div class="device-section">
          <div class="device-current">
            当前设备：<span>{{ currentDeviceId || "未连接" }}</span>
          </div>
          <el-button
            type="success"
            :icon="Tools"
            class="action-btn device-btn"
            @click="$emit('open-device-dialog')"
          >
            设备连接
          </el-button>
          <el-button
            type="primary"
            class="action-btn device-btn"
            :loading="screenshotLoading"
            :disabled="!currentDeviceId"
            @click="$emit('capture-screenshot')"
          >
            截图
          </el-button>
        </div>

        <el-button
          class="action-btn"
          :type="selectionEnabled ? 'warning' : 'default'"
          @click="$emit('toggle-selection')"
        >
          {{ selectionEnabled ? "取消圈选" : "启用圈选" }}
        </el-button>

        <el-tag effect="plain">
          {{ selectionInfo ? selectionInfo.x : 0 }},
          {{ selectionInfo ? selectionInfo.y : 0 }},
          {{ selectionInfo ? selectionInfo.w : 0 }},
          {{ selectionInfo ? selectionInfo.h : 0 }}
        </el-tag>

        <el-button
          class="action-btn"
          type="info"
          :icon="ZoomIn"
          @click="$emit('fit-to-window')"
        >
          自适应缩放
        </el-button>

        <el-button class="action-btn" type="info" @click="$emit('reset-zoom')">
          重置缩放
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Upload, Tools, ZoomIn } from "@element-plus/icons-vue";

defineProps({
  currentDeviceId: {
    type: String,
    default: "",
  },
  screenshotLoading: {
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
});

defineEmits([
  "load-image",
  "open-device-dialog",
  "capture-screenshot",
  "toggle-selection",
  "fit-to-window",
  "reset-zoom",
]);
</script>

<style scoped>
.left-panel {
  display: flex;
  flex-direction: column;
}

.action-btn {
  width: 100%;
  padding: 12px;
  font-size: 14px;
}
</style>
