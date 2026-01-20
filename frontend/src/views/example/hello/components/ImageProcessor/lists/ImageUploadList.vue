<template>
  <div>
    <!-- 隐藏的文件选择框 -->
    <input ref="imageFileInputRef" type="file" accept="image/*" multiple style="display: none"
      @change="handleImageFileSelect" />
    <el-table :data="images" height="205" border style="width: 100%" size="small" empty-text="等待上传图片">
      <el-table-column type="index" label="#" width="50"> </el-table-column>
      <el-table-column label="缩略图">
        <template #default="scope">
          <div class="thumbnail-container">
            <el-image :src="scope.row.url" :preview-src-list="getPreviewSrcList()" :initial-index="scope.$index"
              fit="contain" preview-teleported class="thumbnail-image" />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="70">
        <template #default="scope">
          <el-button type="text" size="small" @click="$emit('remove-image', scope.$index)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="display: flex; justify-content: space-between; margin-top: 5px">
      <el-button type="primary" size="small" style="width: 48%" @click="handleUploadClick">
        上传
      </el-button>
      <el-button type="primary" size="small" style="width: 48%" :loading="screenshotLoading"
        @click="$emit('screenshot-click')">
        截图
      </el-button>
    </div>
    <el-button type="danger" size="small" class="clear-all-btn" @click="$emit('clear-all-images')">
      清空全部
    </el-button>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  images: {
    type: Array,
    default: () => [],
  },
  screenshotLoading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["upload-click", "remove-image", "clear-all-images", "screenshot-click", "images-updated"]);

const imageFileInputRef = ref(null);

// 处理上传按钮点击
const handleUploadClick = () => {
  imageFileInputRef.value?.click();
};

// 处理图片文件选择
const handleImageFileSelect = (event) => {
  const files = Array.from(event.target.files || []);
  if (files.length === 0) return;

  // 过滤出图片文件
  const imageFiles = files.filter((file) => file.type.startsWith("image/"));

  if (imageFiles.length === 0) {
    ElMessage.error("请选择图片文件");
    return;
  }

  const newImages = [];

  // 处理每个图片文件
  imageFiles.forEach((file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const url = e.target.result;

      // 创建缩略图
      const img = new Image();
      img.onload = () => {
        // 创建缩略图 canvas
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const maxSize = 100; // 缩略图最大尺寸

        // 计算缩略图尺寸
        let thumbWidth = img.width;
        let thumbHeight = img.height;
        if (thumbWidth > thumbHeight) {
          if (thumbWidth > maxSize) {
            thumbHeight = (thumbHeight * maxSize) / thumbWidth;
            thumbWidth = maxSize;
          }
        } else {
          if (thumbHeight > maxSize) {
            thumbWidth = (thumbWidth * maxSize) / thumbHeight;
            thumbHeight = maxSize;
          }
        }

        canvas.width = thumbWidth;
        canvas.height = thumbHeight;
        ctx.drawImage(img, 0, 0, thumbWidth, thumbHeight);

        const thumbnail = canvas.toDataURL("image/png");

        // 添加到新图片列表
        newImages.push({
          id: Date.now() + Math.random(), // 生成唯一ID
          url: url,
          thumbnail: thumbnail,
          file: file, // 保存原始文件对象
        });

        // 当所有图片处理完成后，通知父组件
        if (newImages.length === imageFiles.length) {
          emit("images-updated", newImages);
          ElMessage.success(`成功上传 ${newImages.length} 张图片`);
        }
      };
      img.onerror = () => {
        ElMessage.error("图片加载失败");
      };
      img.src = url;
    };
    reader.onerror = () => {
      ElMessage.error("读取文件失败");
    };
    reader.readAsDataURL(file);
  });

  // 清空文件选择，以便可以重复选择同一文件
  event.target.value = "";
};

// 获取预览图片列表
const getPreviewSrcList = () => {
  return props.images.map((img) => img.url);
};

// 暴露文件输入框引用
defineExpose({
  getFileInput: () => imageFileInputRef.value,
});
</script>

<style scoped>
.clear-all-btn {
  width: 100%;
  margin-top: 5px;
}

.thumbnail-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 60px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  background: #f5f5f5;
  transition: all 0.2s ease;
}

.thumbnail-container:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
  transform: scale(1.05);
}

.thumbnail-image {
  width: 100%;
  height: 100%;
}
</style>

