<template>
  <div class="image-processor-tab">
    <!-- 左中右布局 -->
    <div class="processor-layout">
      <!-- 左侧：功能按钮区域 -->
      <div class="left-panel">
        <div class="card">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><Tools /></el-icon>
            </div>
            <h2>功能</h2>
          </div>
          <div class="card-body">
            <el-button 
              type="primary" 
              :icon="Upload"
              @click="handleLoadImage"
              class="action-btn"
            >
              载入图片
            </el-button>
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              multiple
              style="display: none"
              @change="handleFileSelect"
            />
          </div>
        </div>
      </div>

      <!-- 中间：图片显示区域 -->
      <div class="center-panel">
        <div class="card">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><Picture /></el-icon>
            </div>
            <h2>图片预览</h2>
          </div>
          <div class="card-body image-container-wrapper">
            <!-- Tab 切换 -->
            <div v-if="images.length > 0" class="image-tabs">
              <el-tabs 
                v-model="currentImageIndex" 
                type="card"
                closable
                @tab-remove="removeImage"
                class="image-tabs-container"
              >
                <el-tab-pane
                  v-for="(image, index) in images"
                  :key="index"
                  :label="image.name"
                  :name="String(index)"
                >
                </el-tab-pane>
              </el-tabs>
            </div>
            <div 
              class="image-container"
              ref="imageContainerRef"
              @mousemove="handleContainerMouseMove"
              @mouseleave="handleMouseLeave"
              @click="handleImageClick"
            >
              <div v-if="currentImage" class="image-wrapper">
                <img 
                  :src="currentImage.url" 
                  alt="预览图片"
                  ref="imageRef"
                  @load="handleImageLoad"
                  draggable="false"
                />
              </div>
              <div v-else class="empty-placeholder">
                <el-icon class="empty-icon"><Picture /></el-icon>
                <p>请载入图片</p>
              </div>
            </div>
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
                <span class="info-value">{{ currentImage.info.width }} × {{ currentImage.info.height }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：放大镜和颜色信息 -->
      <div class="right-panel">
        <!-- 放大镜 -->
        <div class="card">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><ZoomIn /></el-icon>
            </div>
            <h2>放大镜</h2>
          </div>
          <div class="card-body magnifier-container">
            <div 
              v-if="magnifierVisible && currentImage"
              class="magnifier"
              ref="magnifierRef"
            >
              <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
            </div>
            <div v-else class="magnifier-placeholder">
              <el-icon><ZoomIn /></el-icon>
              <p>将鼠标移动到图片上查看</p>
            </div>
            <!-- 当前颜色值 -->
            <div v-if="currentColor" class="current-color">
              <div class="color-preview" :style="{ backgroundColor: currentColor.hex }"></div>
              <div class="color-values">
                <div class="color-value-item">
                  <span class="color-label">坐标:</span>
                  <span class="color-value">({{ currentPosition.x }}, {{ currentPosition.y }})</span>
                </div>
                <div class="color-value-item">
                  <span class="color-label">RGB:</span>
                  <span class="color-value">{{ currentColor.rgb }}</span>
                </div>
                <div class="color-value-item">
                  <span class="color-label">HEX:</span>
                  <span class="color-value">{{ currentColor.hex }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 选中颜色列表 -->
        <div class="card">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><Collection /></el-icon>
            </div>
            <h2>选中颜色</h2>
            <span class="color-count">{{ currentSelectedColors.length }} 个</span>
          </div>
          <div class="card-body selected-colors-container">
            <div v-if="currentSelectedColors.length === 0" class="empty-colors">
              <el-icon><Collection /></el-icon>
              <p>点击图片记录颜色</p>
            </div>
            <div v-else class="selected-colors-list">
              <div
                v-for="(color, index) in currentSelectedColors"
                :key="index"
                class="selected-color-item"
              >
                <div class="color-preview-small" :style="{ backgroundColor: color.hex }"></div>
                <div class="color-info-small">
                  <div class="color-coord-small">坐标: ({{ color.x }}, {{ color.y }})</div>
                  <div class="color-rgb-small">{{ color.rgb }}</div>
                  <div class="color-hex-small">{{ color.hex }}</div>
                </div>
                <el-button
                  type="danger"
                  size="small"
                  :icon="Delete"
                  circle
                  @click="removeColor(index)"
                  class="remove-color-btn"
                />
              </div>
            </div>
            <el-button
              v-if="currentSelectedColors.length > 0"
              type="danger"
              size="small"
              :icon="Delete"
              @click="clearAllColors"
              class="clear-all-btn"
            >
              清空全部
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { Upload, Picture, ZoomIn, Collection, Delete, Tools } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// 文件输入引用
const fileInputRef = ref(null);
const imageRef = ref(null);
const imageContainerRef = ref(null);
const imageWrapperRef = ref(null);
const magnifierRef = ref(null);
const magnifierCanvasRef = ref(null);

// 图片数组
const images = ref([]);
const currentImageIndex = ref('0');

// 当前图片的计算属性
const currentImage = computed(() => {
  const index = typeof currentImageIndex.value === 'string' ? parseInt(currentImageIndex.value) : currentImageIndex.value;
  if (images.value.length === 0 || isNaN(index) || index < 0 || index >= images.value.length) {
    return null;
  }
  return images.value[index];
});

// 当前图片的URL（用于兼容现有代码）
const imageUrl = computed(() => currentImage.value?.url || null);

// 当前图片的信息（用于兼容现有代码）
const imageInfo = computed(() => currentImage.value?.info || null);

// 当前图片的选中颜色列表
const currentSelectedColors = computed(() => {
  if (!currentImage.value) return [];
  return currentImage.value.selectedColors || [];
});

// 放大镜相关
const magnifierVisible = ref(false);
const mousePosition = ref({ x: 0, y: 0 });
const currentColor = ref(null);
const currentPosition = ref({ x: 0, y: 0 }); // 当前鼠标位置的图片坐标

// 图片尺寸
const imageNaturalSize = ref({ width: 0, height: 0 });

// 载入图片
function handleLoadImage() {
  fileInputRef.value?.click();
}

// 处理文件选择
function handleFileSelect(event) {
  const files = Array.from(event.target.files || []);
  if (files.length === 0) return;

  // 过滤出图片文件
  const imageFiles = files.filter(file => file.type.startsWith('image/'));
  
  if (imageFiles.length === 0) {
    ElMessage.error('请选择图片文件');
    return;
  }

  // 处理每个图片文件
  imageFiles.forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const url = e.target.result;
      
      // 获取图片信息
      const img = new Image();
      img.onload = () => {
        const imageData = {
          name: file.name,
          url: url,
          file: file,
          info: {
            fileSize: formatFileSize(file.size),
            format: file.type.split('/')[1].toUpperCase(),
            width: img.width,
            height: img.height
          },
          selectedColors: []
        };
        
        images.value.push(imageData);
        
        // 如果是第一张图片，自动选中
        if (images.value.length === 1) {
          currentImageIndex.value = '0';
        } else {
          // 切换到新添加的图片
          currentImageIndex.value = String(images.value.length - 1);
        }
        
        // 更新图片尺寸
        if (currentImageIndex.value === images.value.length - 1) {
          imageNaturalSize.value = { width: img.width, height: img.height };
        }
      };
      img.src = url;
    };
    reader.readAsDataURL(file);
  });

  // 清空文件输入，以便可以再次选择相同文件
  event.target.value = '';
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 图片加载完成
function handleImageLoad() {
  if (imageRef.value) {
    imageNaturalSize.value = { 
      width: imageRef.value.naturalWidth, 
      height: imageRef.value.naturalHeight 
    };
  }
}

// 容器鼠标移动处理
function handleContainerMouseMove(event) {
  if (!currentImage.value || !imageRef.value) {
    magnifierVisible.value = false;
    return;
  }
  
  // 确保图片已加载完成
  if (!imageRef.value.complete || imageRef.value.naturalWidth === 0 || imageRef.value.naturalHeight === 0) {
    magnifierVisible.value = false;
    return;
  }

  // 放大镜模式
  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const containerX = event.clientX - containerRect.left;
  const containerY = event.clientY - containerRect.top;

  // 检查鼠标是否在容器内
  if (containerX < 0 || containerX >= containerRect.width || 
      containerY < 0 || containerY >= containerRect.height) {
    magnifierVisible.value = false;
    currentColor.value = null;
    return;
  }

  mousePosition.value = { x: containerX, y: containerY };

  // 计算图片元素的位置
  const imageRect = imageRef.value.getBoundingClientRect();
  
  // 计算鼠标相对于图片元素的坐标
  const imageX = event.clientX - imageRect.left;
  const imageY = event.clientY - imageRect.top;
  
  // 检查是否在图片显示区域内
  if (imageX >= 0 && imageX < imageRect.width && 
      imageY >= 0 && imageY < imageRect.height) {
    // 转换为图片原始尺寸的坐标
    const scaleX = imageRef.value.naturalWidth / imageRect.width;
    const scaleY = imageRef.value.naturalHeight / imageRect.height;
    const naturalX = imageX * scaleX;
    const naturalY = imageY * scaleY;
    
      // 确保坐标在有效范围内
      if (naturalX >= 0 && naturalX < imageRef.value.naturalWidth &&
          naturalY >= 0 && naturalY < imageRef.value.naturalHeight) {
        // 更新当前坐标
        currentPosition.value = {
          x: Math.floor(naturalX),
          y: Math.floor(naturalY)
        };
        magnifierVisible.value = true;
        updateMagnifier(naturalX, naturalY);
        updateCurrentColor(naturalX, naturalY);
      } else {
        magnifierVisible.value = false;
        currentColor.value = null;
        currentPosition.value = { x: 0, y: 0 };
      }
  } else {
    magnifierVisible.value = false;
    currentColor.value = null;
  }
}

// 鼠标离开
function handleMouseLeave() {
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
}

// 更新放大镜（x, y 是图片原始尺寸的坐标）
function updateMagnifier(x, y) {
  if (!magnifierCanvasRef.value || !imageRef.value) return;

  // 确保图片已加载
  if (imageRef.value.naturalWidth === 0 || imageRef.value.naturalHeight === 0) return;

  const canvas = magnifierCanvasRef.value;
  const ctx = canvas.getContext('2d');
  const scale = 10; // 放大倍数
  const size = 11; // 11x11像素
  const halfSize = Math.floor(size / 2);

  canvas.width = size * scale;
  canvas.height = size * scale;

  // 计算源图片坐标（确保在范围内）
  const sourceX = Math.max(0, Math.min(imageRef.value.naturalWidth - size, Math.floor(x - halfSize)));
  const sourceY = Math.max(0, Math.min(imageRef.value.naturalHeight - size, Math.floor(y - halfSize)));

  // 绘制放大区域
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(
    imageRef.value,
    sourceX, sourceY, size, size,
    0, 0, canvas.width, canvas.height
  );

  // 绘制网格（每个像素一个格子）
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
  ctx.lineWidth = 1;
  ctx.lineCap = 'square';
  for (let i = 0; i <= size; i++) {
    const pos = i * scale;
    // 垂直线
    ctx.beginPath();
    ctx.moveTo(pos + 0.5, 0);
    ctx.lineTo(pos + 0.5, canvas.height);
    ctx.stroke();
    // 水平线
    ctx.beginPath();
    ctx.moveTo(0, pos + 0.5);
    ctx.lineTo(canvas.width, pos + 0.5);
    ctx.stroke();
  }

  // 绘制中心十字线（红色，更粗）
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  ctx.strokeStyle = '#ff0000';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(centerX - scale * halfSize, centerY);
  ctx.lineTo(centerX + scale * halfSize, centerY);
  ctx.moveTo(centerX, centerY - scale * halfSize);
  ctx.lineTo(centerX, centerY + scale * halfSize);
  ctx.stroke();
}

// 更新当前颜色（x, y 是图片原始尺寸的坐标）
function updateCurrentColor(x, y) {
  if (!imageRef.value) return;

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = imageRef.value.naturalWidth;
  canvas.height = imageRef.value.naturalHeight;
  ctx.drawImage(imageRef.value, 0, 0);

  const imageX = Math.floor(x);
  const imageY = Math.floor(y);

  if (imageX >= 0 && imageX < canvas.width && imageY >= 0 && imageY < canvas.height) {
    const imageData = ctx.getImageData(imageX, imageY, 1, 1);
    const [r, g, b] = imageData.data;
    const hex = `#${[r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')}`;
    
    currentColor.value = {
      rgb: `rgb(${r}, ${g}, ${b})`,
      hex: hex.toUpperCase()
    };
  }
}

// 图片点击处理
function handleImageClick(event) {
  if (!currentImage.value || !imageRef.value || !currentColor.value) return;

  const imageRect = imageRef.value.getBoundingClientRect();
  const imageX = event.clientX - imageRect.left;
  const imageY = event.clientY - imageRect.top;

  if (imageX >= 0 && imageX < imageRect.width && imageY >= 0 && imageY < imageRect.height) {
    // 转换为图片原始尺寸的坐标
    const scaleX = imageRef.value.naturalWidth / imageRect.width;
    const scaleY = imageRef.value.naturalHeight / imageRect.height;
    const naturalX = Math.floor(imageX * scaleX);
    const naturalY = Math.floor(imageY * scaleY);
    
    // 确保当前图片有颜色数组
    if (!currentImage.value.selectedColors) {
      currentImage.value.selectedColors = [];
    }
    
    // 记录颜色到当前图片
    currentImage.value.selectedColors.push({
      ...currentColor.value,
      x: naturalX,
      y: naturalY
    });
  }
}

// 移除颜色
function removeColor(index) {
  if (currentImage.value && currentImage.value.selectedColors) {
    currentImage.value.selectedColors.splice(index, 1);
  }
}

// 清空所有颜色
function clearAllColors() {
  if (currentImage.value && currentImage.value.selectedColors) {
    currentImage.value.selectedColors = [];
  }
}

// 移除图片
function removeImage(index) {
  const removeIndex = typeof index === 'string' ? parseInt(index) : index;
  
  if (images.value.length <= 1) {
    ElMessage.warning('至少需要保留一张图片');
    return;
  }
  
  images.value.splice(removeIndex, 1);
  
  // 调整当前索引
  const currentIndex = typeof currentImageIndex.value === 'string' ? parseInt(currentImageIndex.value) : currentImageIndex.value;
  
  if (currentIndex >= images.value.length) {
    currentImageIndex.value = String(images.value.length - 1);
  } else if (currentIndex > removeIndex) {
    currentImageIndex.value = String(currentIndex - 1);
  } else if (currentIndex === removeIndex) {
    // 如果删除的是当前图片，切换到前一张或后一张
    currentImageIndex.value = String(Math.min(removeIndex, images.value.length - 1));
  }
  
  // 重置放大镜和颜色
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
}

// 监听当前图片切换，重置放大镜和颜色
watch(currentImageIndex, () => {
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
  
  if (currentImage.value) {
    nextTick(() => {
      if (imageRef.value) {
        imageNaturalSize.value = {
          width: imageRef.value.naturalWidth,
          height: imageRef.value.naturalHeight
        };
      }
    });
  }
});
</script>

<style scoped>
.image-processor-tab {
  width: 100%;
}

.processor-layout {
  display: grid;
  grid-template-columns: 200px 1fr 300px;
  gap: 24px;
  min-height: calc(100vh - 200px);
}

/* 卡片通用样式 */
.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
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
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  color: white;
}

.card-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
}

/* 左侧面板 */
.left-panel {
  display: flex;
  flex-direction: column;
}

.action-btn {
  width: 100%;
  padding: 12px;
  font-size: 14px;
}

/* 中间面板 */
.center-panel {
  display: flex;
  flex-direction: column;
}

.image-container-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 800px;
  overflow-x: hidden;
}

.image-tabs {
  margin-bottom: 16px;
  max-width: 800px;
  overflow: hidden;
}

.image-tabs-container {
  width: 100%;
}

.image-tabs-container :deep(.el-tabs__header) {
  margin: 0;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0;
}

/* 隐藏左右滚动按钮 */
.image-tabs-container :deep(.el-tabs__nav-prev),
.image-tabs-container :deep(.el-tabs__nav-next) {
  display: none !important;
}

.image-tabs-container :deep(.el-tabs__nav-wrap) {
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(99, 102, 241, 0.3) transparent;
  /* 固定高度，为滚动条预留空间 */
  min-height: 42px;
  height: 42px;
  padding-bottom: 0;
  margin-bottom: 0;
}

.image-tabs-container :deep(.el-tabs__nav-wrap::-webkit-scrollbar) {
  height: 6px;
}

.image-tabs-container :deep(.el-tabs__nav-wrap::-webkit-scrollbar-track) {
  background: transparent;
}

.image-tabs-container :deep(.el-tabs__nav-wrap::-webkit-scrollbar-thumb) {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 3px;
}

.image-tabs-container :deep(.el-tabs__nav-wrap::-webkit-scrollbar-thumb:hover) {
  background: rgba(99, 102, 241, 0.5);
}

.image-tabs-container :deep(.el-tabs__nav-scroll) {
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 0;
  height: 100%;
}

/* 确保 nav-wrap 有固定高度，避免滚动条影响布局 */
.image-tabs-container :deep(.el-tabs__nav-wrap.is-scrollable) {
  padding-bottom: 0;
  margin-bottom: 0;
  min-height: 42px;
  height: 42px;
}

.image-tabs-container :deep(.el-tabs__nav) {
  white-space: nowrap;
  display: flex;
  align-items: flex-end;
  gap: 6px;
  margin-bottom: 0;
  padding-bottom: 0;
  height: 36px;
  box-sizing: border-box;
}

.image-tabs-container :deep(.el-tabs__item) {
  padding: 0 16px;
  height: 36px;
  line-height: 36px;
  font-size: 13px;
  white-space: nowrap;
  flex-shrink: 0;
  width: auto;
  min-width: auto;
  max-width: none;
  overflow: visible;
  text-overflow: clip;
  margin-right: 0 !important;
  margin-left: 0 !important;
  border-radius: 4px 4px 0 0;
  transition: all 0.2s ease;
  position: relative;
  display: inline-block;
  border: 1px solid var(--border-color);
  background: rgba(51, 65, 85, 0.3);
}

.image-tabs-container :deep(.el-tabs__item:hover) {
  background: rgba(51, 65, 85, 0.5);
}

.image-tabs-container :deep(.el-tabs__active-bar) {
  display: none;
}

.image-tabs-container :deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
  border-bottom-color: transparent;
}

.image-tabs-container :deep(.el-tabs__item .el-icon-close) {
  margin-left: 8px;
  font-size: 12px;
  width: 14px;
  height: 14px;
  transition: color 0.2s ease;
}

.image-tabs-container :deep(.el-tabs__item .el-icon-close:hover) {
  color: var(--primary-color);
}

.image-container {
  width: 800px;
  height: 600px;
  min-width: 800px;
  min-height: 600px;
  max-width: 800px;
  max-height: 600px;
  border: 2px solid var(--border-color);
  border-radius: 0;
  overflow: auto;
  background: #1a1a2e;
  background-image: 
    linear-gradient(45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(-45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #2a2a3e 75%),
    linear-gradient(-45deg, transparent 75%, #2a2a3e 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  position: relative;
  cursor: crosshair;
  user-select: none;
  flex-shrink: 0;
  box-sizing: border-box;
}

.image-wrapper {
  display: inline-block;
  position: relative;
}

.image-wrapper img {
  display: block;
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  user-select: none;
  pointer-events: none;
  border-radius: 0;
}

.empty-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-placeholder p {
  margin: 0;
  font-size: 14px;
}

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

/* 右侧面板 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.magnifier-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-height: 200px;
}

.magnifier {
  width: 220px;
  height: 220px;
  border: 2px solid var(--primary-color);
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a2e;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.magnifier-canvas {
  width: 100%;
  height: 100%;
  image-rendering: pixelated;
}

.magnifier-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 220px;
  height: 220px;
  color: var(--text-secondary);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
}

.magnifier-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.magnifier-placeholder p {
  margin: 0;
  font-size: 12px;
}

.current-color {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
}

.color-preview {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  border: 2px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.color-values {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.color-value-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.color-label {
  color: var(--text-secondary);
}

.color-value {
  color: var(--text-primary);
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.color-count {
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(99, 102, 241, 0.2);
  padding: 4px 10px;
  border-radius: 12px;
}

.selected-colors-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.empty-colors {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.empty-colors .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-colors p {
  margin: 0;
  font-size: 14px;
}

.selected-colors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selected-color-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.selected-color-item:hover {
  background: rgba(51, 65, 85, 0.5);
}

.color-preview-small {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}

.color-info-small {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.color-rgb-small,
.color-hex-small {
  font-size: 12px;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
}

.color-hex-small {
  color: var(--text-secondary);
}

.color-coord-small {
  font-size: 11px;
  color: var(--primary-light);
  font-weight: 500;
  margin-bottom: 2px;
}

.remove-color-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.selected-color-item:hover .remove-color-btn {
  opacity: 1;
}

.clear-all-btn {
  width: 100%;
  margin-top: 8px;
}

/* 响应式布局 */
@media (max-width: 1400px) {
  .processor-layout {
    grid-template-columns: 180px 1fr 280px;
  }
}

@media (max-width: 1200px) {
  .processor-layout {
    grid-template-columns: 1fr;
  }
  
  .right-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
</style>

