<template>
  <div class="image-processing-layout">
    <div class="left-panel">
      <ImageUploadCard @image-change="handleImageChange" />
      <PipelineStepList
        @process="handlePipelineProcess"
        :can-process="Boolean(imageId)"
        :image-src="displayImageSrc"
        :image-id="imageId"
      />
    </div>
    <div class="right-panel">
      <ImageShow :image-src="displayImageSrc" />
    </div>
  </div>
</template>

<script setup>
import { ref, inject, watch } from "vue";
import ImageUploadCard from "./ImageUploadCard.vue";
import ImageShow from "./ImageShow.vue";
import PipelineStepList from "./PipelineStepList.vue";

const sendToBackend = inject("sendToBackend", null);
const imageProcessingResult = inject("imageProcessingResult", null);
const imageUploadedInfo = inject("imageUploadedInfo", null);

const originalImageSrc = ref("");
const imageId = ref("");
const displayImageSrc = ref("");

/**
 * 接收子组件上传结果：{ path, preview }
 * - preview 仅用于前端展示
 * - path 发送给后端，由后端自行读取磁盘文件
 */
const handleImageChange = (payload) => {
  const safePayload = payload || {};
  const path = safePayload.path || "";

  if (sendToBackend && path) {
    sendToBackend("图像上传缓存", {
      图片路径: path,
    });
  }
};

const handlePipelineProcess = (steps) => {
  if (!sendToBackend || !imageId.value) {
    return;
  }
  sendToBackend("图像处理流水线", {
    imageId: imageId.value,
    步骤: JSON.parse(JSON.stringify(steps)),
  });
};

if (imageProcessingResult) {
  watch(
    imageProcessingResult,
    (val) => {
      if (val && typeof val === "string") {
        displayImageSrc.value = val;
      }
    },
    { immediate: false }
  );
}

if (imageUploadedInfo) {
  watch(
    imageUploadedInfo,
    (val) => {
      if (val && typeof val.imageId === "string") {
        imageId.value = val.imageId;
        displayImageSrc.value = val.preview;
      }
    },
    { immediate: false, deep: true }
  );
}
</script>

<style scoped>
.image-processing-layout {
  display: flex;
  height: 100%;
  box-sizing: border-box;
  padding: 16px;
  gap: 16px;
}

.left-panel {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.right-panel {
  flex: 1;
  min-width: 0;
}
</style>
