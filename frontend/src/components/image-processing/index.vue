<template>
  <div class="image-processing-layout">
    <div class="left-panel">
      <ImageUploadCard />
      <PipelineStepList />
    </div>
    <div class="right-panel">
      <ImageShow />
    </div>
  </div>
</template>

<script setup>
import ImageUploadCard from "./ImageUploadCard.vue";
import ImageShow from "./ImageShow.vue";
import PipelineStepList from "./PipelineStepList.vue";
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
