<template>
  <div class="content-layout">
    <!-- 左侧：处理模块配置区 -->
    <div class="modules-panel">
      <ImageUploadCard
        :image-file-name="imageFileName"
        @image-select="handleImageSelect"
      />

      <ColorFilterCard
        :image-loaded="imageLoaded"
        :keep-colors="keepColors"
        :filter-colors="filterColors"
        :get-color-preview="getColorPreview"
        @add-step="addColorFilterStep"
        @add-keep-color="addKeepColor"
        @remove-keep-color="removeKeepColor"
        @update-keep-color="updateKeepColor"
        @add-filter-color="addFilterColor"
        @remove-filter-color="removeFilterColor"
        @update-filter-color="updateFilterColor"
      />

      <BinaryCard
        :image-loaded="imageLoaded"
        v-model:threshold="threshold"
        @add-step="addBinaryStep"
      />

      <FloodFillCard
        :image-loaded="imageLoaded"
        :flood-fill-start-point="floodFillStartPoint"
        @add-step="addFloodFillStep"
      />
    </div>

    <!-- 右侧：处理步骤列表 -->
    <div class="steps-panel">
      <ProcessingStepsCard
        :processing-steps="processingSteps"
        :drag-index="dragIndex"
        :image-loaded="imageLoaded"
        :processing="processing"
        @remove-step="removeStep"
        @clear-all="clearAllSteps"
        @start-processing="startProcessing"
        @drag-start="handleDragStart"
        @drag-over="handleDragOver"
        @drag-end="handleDragEnd"
        @drop="handleDrop"
        @show-flood-animation="showFloodFillAnimation"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useColoring } from '../composables/useColoring';
import ImageUploadCard from './ImageUploadCard.vue';
import ColorFilterCard from './ColorFilterCard.vue';
import BinaryCard from './BinaryCard.vue';
import FloodFillCard from './FloodFillCard.vue';
import ProcessingStepsCard from './ProcessingStepsCard.vue';

const {
  // 状态
  imageFileName,
  threshold,
  processing,
  imageLoaded,
  floodFillStartPoint,
  keepColors,
  filterColors,
  processingSteps,
  currentStepIndex,
  dragIndex,
  
  // 方法
  getColorPreview,
  handleImageSelect,
  handleSaveImage,
  addKeepColor,
  removeKeepColor,
  addFilterColor,
  removeFilterColor,
  addColorFilterStep,
  addBinaryStep,
  addFloodFillStep,
  removeStep,
  clearAllSteps,
  handleDragStart,
  handleDragOver,
  handleDrop,
  handleDragEnd,
  startProcessing,
  showFloodFillAnimation,
  
  // 生命周期
  initSocket,
  initIpcListeners,
  cleanup
} = useColoring();

// 更新颜色
function updateKeepColor(index, value) {
  keepColors.value[index] = value;
}

function updateFilterColor(index, value) {
  filterColors.value[index] = value;
}

// 暴露给父组件
defineExpose({
  handleSaveImage,
  processing,
  imageLoaded
});

onMounted(() => {
  initSocket();
  initIpcListeners();
});

onUnmounted(() => {
  cleanup();
});
</script>

<style scoped>
.content-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
}

.modules-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.steps-panel {
  position: sticky;
  top: 100px;
  height: fit-content;
}

@media (max-width: 1200px) {
  .content-layout {
    grid-template-columns: 1fr;
  }
  
  .steps-panel {
    position: static;
  }
}
</style>
