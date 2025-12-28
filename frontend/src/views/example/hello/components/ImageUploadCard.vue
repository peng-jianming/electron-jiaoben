<template>
  <section class="card upload-card">
    <div class="card-header">
      <div class="card-icon upload-icon">
        <el-icon><Upload /></el-icon>
      </div>
      <h2>图像加载</h2>
    </div>
    <div class="card-body">
      <el-upload
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleImageSelect"
        accept="image/*"
        drag
        class="upload-dragger"
      >
        <div class="upload-content">
          <el-icon class="upload-big-icon"><Upload /></el-icon>
          <div class="upload-text">
            <p class="primary-text">拖拽图像文件到此处</p>
            <p class="secondary-text">或点击选择文件</p>
          </div>
        </div>
      </el-upload>
      <div v-if="imageFileName" class="file-info">
        <el-icon><Document /></el-icon>
        <span>{{ imageFileName }}</span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Upload, Document } from '@element-plus/icons-vue';

defineProps({
  imageFileName: String
});

const emit = defineEmits(['image-select']);

function handleImageSelect(file) {
  emit('image-select', file);
}
</script>

<style scoped>
.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: var(--shadow-lg);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.3);
  border-bottom: 1px solid var(--border-color);
}

.card-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}

.card-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.upload-icon {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  color: white;
}

.card-body {
  padding: 20px;
}

.upload-card {
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(59, 130, 246, 0.05) 100%);
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  background: transparent;
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  transition: all 0.3s ease;
  padding: 40px 20px;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-big-icon {
  font-size: 48px;
  color: var(--primary-light);
}

.upload-text {
  text-align: center;
}

.primary-text {
  font-size: 16px;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.secondary-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
  color: var(--primary-light);
  font-size: 14px;
}
</style>

