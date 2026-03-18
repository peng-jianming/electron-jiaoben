<template>
  <div class="upload-card">
    <div class="upload-header">图片上传</div>
    <div
      class="upload-area"
      @dragover.prevent
      @drop.prevent="onDrop"
      @click="onClickSelect"
    >
      <input
        ref="fileInputRef"
        type="file"
        accept="image/*"
        class="file-input"
        @change="onFileChange"
      />
      <div class="upload-hint">
        <div>点击或拖拽图片到此处上传</div>
        <div class="upload-sub-hint">支持常见图片格式（JPG/PNG/WebP 等）</div>
      </div>
    </div>
    <div v-if="fileName" class="file-info">
      当前选择：{{ fileName }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useImageProcessingStore } from '@/stores/imageProcessing';

const fileInputRef = ref(null);
const fileName = ref('');
const imageProcessingStore = useImageProcessingStore();

// 仅在前端本地生成预览，不再把 base64 发给后端
const readFileAsDataUrl = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });
};

const handleFile = async (file) => {
  if (!file) return;
  fileName.value = file.name;

  const filePath = file.path || '';
  let preview = '';

  try {
    // 预览仍然使用 dataUrl，但只在前端本地使用
    preview = await readFileAsDataUrl(file);
  } catch (e) {
    console.error('读取图片失败', e);
    preview = '';
  }

  // 直接交给全局 store 处理
  imageProcessingStore.handleImageChange({
    path: filePath,
    preview,
  });
};

const onFileChange = async (event) => {
  const files = event.target.files;
  if (!files || !files.length) return;
  await handleFile(files[0]);
  // 清空 input，方便再次选择同一张图片也能触发 change
  event.target.value = '';
};

const onDrop = async (event) => {
  const files = event.dataTransfer?.files;
  if (!files || !files.length) return;
  await handleFile(files[0]);
};

const onClickSelect = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click();
  }
};
</script>

<style scoped>
.upload-card {
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 12px;
  background-color: #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.upload-header {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.upload-area {
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  padding: 20px 12px;
  text-align: center;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.upload-area:hover {
  border-color: #3b82f6;
  background-color: #f1f5f9;
}

.upload-sub-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #9ca3af;
}

.file-input {
  display: none;
}

.file-info {
  margin-top: 8px;
  font-size: 12px;
  color: #4b5563;
}
</style>
