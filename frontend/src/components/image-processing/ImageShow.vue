<template>
  <div class="image-show">
    <div v-if="!displayImageSrc" class="placeholder">
      暂无图片，请先在左侧上传
    </div>
    <div v-else class="image-wrapper">
      <img :src="displayImageSrc" alt="预览图片" class="image" />
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from "pinia";
import { useImageProcessingStore } from "@/stores/imageProcessing";

const imageProcessingStore = useImageProcessingStore();
const { displayImageSrc } = storeToRefs(imageProcessingStore);
</script>

<style scoped>
.image-show {
  width: 100%;
  height: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 12px;
}

.placeholder {
  font-size: 14px;
  color: #9ca3af;
}

.image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
}
</style>