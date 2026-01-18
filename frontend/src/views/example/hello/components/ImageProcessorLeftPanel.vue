<template>
  <div class="left-panel">
    <el-button type="primary" @click="$emit('open-device-dialog')"> 设备连接 </el-button>

    <el-tag effect="plain">
      当前设备：{{ currentDeviceId || "未连接" }}
    </el-tag>

    <el-button
      type="primary"
      :loading="screenshotLoading"
      :disabled="!currentDeviceId"
      @click="$emit('capture-screenshot')"
    >
      截图
    </el-button>

    <el-divider></el-divider>

    <el-button type="primary" @click="$emit('load-image')"> 载入图片 </el-button>

    <el-button 
      type="success" 
      :disabled="!hasImage"
      @click="$emit('save-image')"
    >
      保存图片
    </el-button>

    <el-divider></el-divider>

    <el-button
      :type="selectionEnabled ? 'warning' : 'primary'"
      @click="$emit('toggle-selection')"
    >
      {{ selectionEnabled ? "取消选取" : "启用选取(颜色|范围)" }}
    </el-button>

    <el-tag effect="plain">
      {{ selectionInfo ? selectionInfo.x : 0 }},
      {{ selectionInfo ? selectionInfo.y : 0 }},
      {{ selectionInfo ? selectionInfo.w : 0 }},
      {{ selectionInfo ? selectionInfo.h : 0 }}
    </el-tag>

    <el-button 
      type="warning" 
      :disabled="!hasImage || !selectionInfo"
      @click="$emit('crop-image')"
    >
      裁剪图片
    </el-button>

    <el-divider></el-divider>

    <el-button type="primary" @click="$emit('fit-to-window')"> 自适应缩放 </el-button>

    <el-button type="primary" @click="$emit('reset-zoom')"> 重置缩放 </el-button>
  </div>
</template>

<script setup>

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
  hasImage: {
    type: Boolean,
    default: false,
  },
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
]);
</script>

<style scoped>
.left-panel {
  display: flex;
  flex-direction: column;
  width: 200px;
  gap: 5px;
  padding: 0 5px;
}
.el-button+.el-button {
    margin-left: 0;
}
</style>
