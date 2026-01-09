<template>
  <div class="info-panel">
    <!-- 图片信息 -->
    <div v-if="currentImage && currentImage.info" class="image-info">
      <div class="info-item">
        <span class="info-label">图片大小：</span>
        <span class="info-value">{{ currentImage.info.fileSize }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">图片格式：</span>
        <span class="info-value">{{ currentImage.info.format }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">分辨率：</span>
        <span class="info-value">
          {{ currentImage.info.width }} × {{ currentImage.info.height }}
        </span>
      </div>
    </div>

    <!-- 圈选区域信息 -->
    <div v-if="selectionInfo" class="selection-info">
      <span class="info-label">选区：</span>
      <span class="info-value">
        x={{ selectionInfo.x }}, y={{ selectionInfo.y }}, w={{ selectionInfo.w }}, h={{ selectionInfo.h }}
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentImage: {
    type: Object,
    default: null
  },
  selectionInfo: {
    type: Object,
    default: null
  }
});
</script>

<style scoped>
.image-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.info-label {
  color: var(--text-secondary);
}

.info-value {
  color: var(--text-primary);
  font-weight: 500;
}

.selection-info {
  margin-top: 8px;
  font-size: 13px;
}
</style>


