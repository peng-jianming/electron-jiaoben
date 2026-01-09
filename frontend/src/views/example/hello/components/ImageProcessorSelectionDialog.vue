<template>
  <el-dialog
    v-model="innerVisible"
    title="圈选区域预览"
    width="1366px"
    :close-on-click-modal="false"
    @closed="handleDialogClosed"
    class="selection-dialog"
  >
    <div v-if="croppedImageUrl" class="selection-dialog-layout">
      <!-- 左侧：功能按钮区域 -->
      <div class="left-panel">
        <div class="card">
          <div class="card-body">
            <el-button
              type="primary"
              :icon="Download"
              @click="handleSaveImage"
              :loading="saving"
              class="action-btn"
            >
              保存图片
            </el-button>
            <el-button
              type="default"
              :icon="ZoomIn"
              @click="handleZoomIn"
              :disabled="zoomScale >= 5"
              class="action-btn zoom-btn"
            >
              放大
            </el-button>
            <el-button
              type="default"
              @click="handleResetZoom"
              class="action-btn zoom-btn"
            >
              1:1
            </el-button>
            <el-button
              type="default"
              :icon="ZoomOut"
              @click="handleZoomOut"
              :disabled="zoomScale <= 1"
              class="action-btn zoom-btn"
            >
              缩小
            </el-button>
            <div class="zoom-info">
              当前缩放: {{ Math.round(zoomScale * 100) }}%
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：图片显示区域 -->
      <div class="center-panel">
        <div class="card">
          <div class="card-body image-container-wrapper">
            <div
              class="image-container"
              ref="imageContainerRef"
              @mousemove="handleContainerMouseMove"
              @mouseleave="handleMouseLeave"
            >
              <img
                :src="croppedImageUrl"
                alt="圈选区域预览"
                ref="imageRef"
                @load="handleImageLoad"
                draggable="false"
                class="preview-image"
                :style="{
                  transform: `scale(${zoomScale})`,
                  transformOrigin: 'center center'
                }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：放大镜区域 -->
      <div class="right-panel">
        <div class="card">
          <div class="card-body magnifier-container">
            <div
              v-if="magnifierVisible && croppedImageUrl"
              class="magnifier"
            >
              <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
            </div>
            <div v-else class="magnifier-placeholder">
              <el-icon><ZoomIn /></el-icon>
              <p>将鼠标移动到图片上查看</p>
            </div>
            <!-- 当前颜色值 -->
            <div class="current-color">
              <div class="color-values">
                <div class="color-value-item">
                  <span class="color-label">坐标:</span>
                  <span class="color-value">
                    ({{ currentPosition.x }}, {{ currentPosition.y }})
                  </span>
                </div>
                <div class="color-value-item">
                  <span class="color-label">RGB:</span>
                  <span class="color-value">{{ currentColor ? currentColor.rgb : '--' }}</span>
                </div>
                <div class="color-value-item">
                  <span class="color-label">HEX:</span>
                  <span class="color-value">{{ currentColor ? currentColor.hex : '--' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-preview">
      <el-empty description="暂无预览图片" />
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue';
import { Download, ZoomIn, ZoomOut } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { ipc } from '@/utils/ipcRenderer';
import { ipcApiRoute } from '@/api';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  croppedImageUrl: {
    type: String,
    default: null
  }
});

const emits = defineEmits(['update:visible']);

const innerVisible = computed({
  get: () => props.visible,
  set: (val) => emits('update:visible', val)
});

// 图片引用
const imageRef = ref(null);
const imageContainerRef = ref(null);
const magnifierCanvasRef = ref(null);

// 放大镜相关
const magnifierVisible = ref(false);
const currentColor = ref(null);
const currentPosition = ref({ x: 0, y: 0 });

// 图片尺寸
const imageNaturalSize = ref({ width: 0, height: 0 });

// 保存状态
const saving = ref(false);

// 缩放比例（1.0 = 100%，5.0 = 500%）
const zoomScale = ref(1.0);

// 图片加载完成
function handleImageLoad() {
  console.log('图片加载完成', {
    naturalWidth: imageRef.value?.naturalWidth,
    naturalHeight: imageRef.value?.naturalHeight
  });
  if (imageRef.value) {
    imageNaturalSize.value = {
      width: imageRef.value.naturalWidth,
      height: imageRef.value.naturalHeight
    };
  }
}

// 容器鼠标移动处理（在整个容器区域内都显示放大镜）
function handleContainerMouseMove(event) {
  if (!imageRef.value || !props.croppedImageUrl || !imageContainerRef.value) {
    magnifierVisible.value = false;
    return;
  }

  // 确保图片已加载完成
  if (!imageRef.value.complete || imageRef.value.naturalWidth === 0 || imageRef.value.naturalHeight === 0) {
    magnifierVisible.value = false;
    return;
  }

  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const imageRect = imageRef.value.getBoundingClientRect();
  
  // 计算鼠标相对于容器的位置
  const containerX = event.clientX - containerRect.left;
  const containerY = event.clientY - containerRect.top;
  
  // 计算鼠标相对于图片的位置
  const imageX = event.clientX - imageRect.left;
  const imageY = event.clientY - imageRect.top;

  // 转换为图片原始尺寸的坐标
  const scaleX = imageRef.value.naturalWidth / imageRect.width;
  const scaleY = imageRef.value.naturalHeight / imageRect.height;
  
  // 计算自然坐标，如果超出图片范围，则限制到边缘
  let naturalX = imageX * scaleX;
  let naturalY = imageY * scaleY;
  
  // 限制到图片范围内（边缘像素）
  naturalX = Math.max(0, Math.min(naturalX, imageRef.value.naturalWidth - 1));
  naturalY = Math.max(0, Math.min(naturalY, imageRef.value.naturalHeight - 1));

  // 更新当前坐标
  currentPosition.value = {
    x: Math.floor(naturalX),
    y: Math.floor(naturalY)
  };
  
  magnifierVisible.value = true;
  // 使用 nextTick 确保 canvas 已渲染
  nextTick(() => {
    updateMagnifier(naturalX, naturalY);
  });
  updateCurrentColor(naturalX, naturalY);
}

// 鼠标离开图片
function handleMouseLeave() {
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
}

// 更新放大镜（x, y 是图片原始尺寸的坐标）
function updateMagnifier(x, y) {
  if (!magnifierCanvasRef.value || !imageRef.value) {
    // 如果 canvas 还未渲染，延迟重试
    setTimeout(() => {
      const retryCanvas = magnifierCanvasRef.value;
      if (retryCanvas && imageRef.value) {
        drawMagnifier(retryCanvas, x, y);
      }
    }, 10);
    return;
  }

  // 确保图片已加载
  if (imageRef.value.naturalWidth === 0 || imageRef.value.naturalHeight === 0) return;

  const canvas = magnifierCanvasRef.value;
  drawMagnifier(canvas, x, y);
}

// 绘制放大镜内容
function drawMagnifier(canvas, x, y) {
  if (!canvas || !imageRef.value) return;

  const ctx = canvas.getContext('2d');
  const scale = 10; // 放大倍数
  const size = 11; // 11x11像素
  const halfSize = Math.floor(size / 2);

  const imgWidth = imageRef.value.naturalWidth;
  const imgHeight = imageRef.value.naturalHeight;

  // 鼠标位置对应的像素坐标（中心像素）
  const centerPixelX = Math.floor(x);
  const centerPixelY = Math.floor(y);

  // 计算理想的源坐标（以鼠标位置为中心）
  const idealSourceX = centerPixelX - halfSize;
  const idealSourceY = centerPixelY - halfSize;

  // 计算实际可用的源坐标（处理边界情况）
  let sourceX = Math.max(0, Math.min(idealSourceX, imgWidth - size));
  let sourceY = Math.max(0, Math.min(idealSourceY, imgHeight - size));

  // 如果图片太小，无法显示完整的 size x size 区域
  if (imgWidth < size) {
    sourceX = 0;
  }
  if (imgHeight < size) {
    sourceY = 0;
  }

  // 计算实际可用的尺寸
  const sourceW = Math.min(size, imgWidth - sourceX);
  const sourceH = Math.min(size, imgHeight - sourceY);

  canvas.width = size * scale;
  canvas.height = size * scale;

  // 先清除画布（用黑色背景）
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // 计算中心像素在源区域中的偏移
  const centerOffsetX = centerPixelX - sourceX;
  const centerOffsetY = centerPixelY - sourceY;

  // 计算绘制位置，使得中心像素显示在canvas中心
  // canvas中心位置
  const canvasCenterX = canvas.width / 2;
  const canvasCenterY = canvas.height / 2;
  
  // 计算绘制起始位置，使得中心像素在canvas中心
  const drawX = canvasCenterX - centerOffsetX * scale - scale / 2;
  const drawY = canvasCenterY - centerOffsetY * scale - scale / 2;

  // 绘制放大区域
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(
    imageRef.value,
    sourceX, sourceY, sourceW, sourceH,
    drawX, drawY, sourceW * scale, sourceH * scale
  );

  // 绘制网格（每个像素一个格子）
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
  ctx.lineWidth = 1;
  ctx.lineCap = 'square';
  
  // 计算网格的起始位置（与图片对齐）
  const gridStartX = drawX;
  const gridStartY = drawY;
  const gridEndX = drawX + sourceW * scale;
  const gridEndY = drawY + sourceH * scale;
  
  // 绘制垂直线
  for (let i = 0; i <= sourceW; i++) {
    const pos = gridStartX + i * scale;
    if (pos >= 0 && pos <= canvas.width) {
      ctx.beginPath();
      ctx.moveTo(pos + 0.5, Math.max(0, gridStartY));
      ctx.lineTo(pos + 0.5, Math.min(canvas.height, gridEndY));
      ctx.stroke();
    }
  }
  
  // 绘制水平线
  for (let i = 0; i <= sourceH; i++) {
    const pos = gridStartY + i * scale;
    if (pos >= 0 && pos <= canvas.height) {
      ctx.beginPath();
      ctx.moveTo(Math.max(0, gridStartX), pos + 0.5);
      ctx.lineTo(Math.min(canvas.width, gridEndX), pos + 0.5);
      ctx.stroke();
    }
  }

  // 中心十字线始终在canvas中心
  ctx.strokeStyle = '#ff0000';
  ctx.lineWidth = 2;
  ctx.beginPath();
  // 水平线（从中心向两边延伸）
  ctx.moveTo(canvasCenterX - scale * halfSize, canvasCenterY);
  ctx.lineTo(canvasCenterX + scale * halfSize, canvasCenterY);
  // 垂直线（从中心向上下延伸）
  ctx.moveTo(canvasCenterX, canvasCenterY - scale * halfSize);
  ctx.lineTo(canvasCenterX, canvasCenterY + scale * halfSize);
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

// 保存图片
async function handleSaveImage() {
  console.log('保存图片: 开始', { croppedImageUrl: props.croppedImageUrl ? '存在' : '不存在' });
  
  if (!props.croppedImageUrl) {
    ElMessage.warning('没有可保存的图片');
    return;
  }

  try {
    saving.value = true;

    // 打开保存对话框
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const defaultName = `selection_${timestamp}.png`;

    console.log('保存图片: 打开保存对话框');
    const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
      defaultName: defaultName
    });

    console.log('保存图片: 对话框结果', result);

    if (!result || !result.success || result.canceled) {
      console.log('保存图片: 用户取消或对话框失败');
      saving.value = false;
      return;
    }

    // 从 base64 URL 中提取 base64 字符串（去掉 data:image/png;base64, 前缀）
    let base64Data = props.croppedImageUrl;
    if (base64Data.includes(',')) {
      base64Data = base64Data.split(',')[1];
    }

    console.log('保存图片: 调用保存方法', { filePath: result.filePath, dataLength: base64Data.length });

    // 通过 IPC 调用主进程保存文件
    const saveResult = await ipc.invoke(ipcApiRoute.saveBase64Image, {
      filePath: result.filePath,
      imageData: base64Data
    });

    console.log('保存图片: 保存结果', saveResult);

    if (saveResult && saveResult.success) {
      ElMessage.success('图片保存成功');
    } else {
      throw new Error(saveResult?.error || '保存失败');
    }
  } catch (error) {
    console.error('保存图片失败:', error);
    ElMessage.error(`保存失败: ${error.message || '未知错误'}`);
  } finally {
    saving.value = false;
  }
}

// 放大图片
function handleZoomIn() {
  if (zoomScale.value < 5.0) {
    zoomScale.value = Math.min(5.0, zoomScale.value + 0.25);
  }
}

// 缩小图片
function handleZoomOut() {
  if (zoomScale.value > 1.0) {
    zoomScale.value = Math.max(1.0, zoomScale.value - 0.25);
  }
}

// 重置为1:1
function handleResetZoom() {
  zoomScale.value = 1.0;
}

// 弹框关闭时重置状态
function handleDialogClosed() {
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
  zoomScale.value = 1.0;
}
</script>

<style scoped>
.selection-dialog-layout {
  display: grid;
  grid-template-columns: 200px 800px 300px;
  gap: 20px;
  height: 600px;
}

.left-panel {
  display: flex;
  flex-direction: column;
}

.center-panel {
  display: flex;
  flex-direction: column;
  width: 800px;
  flex-shrink: 0;
}

.right-panel {
  display: flex;
  flex-direction: column;
}

.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: var(--shadow-lg);
}

.card-body {
  padding: 20px;
  flex: 1;
  overflow: hidden;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.image-container-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  height: 100%;
  overflow: hidden;
  padding: 0;
  flex: 1;
  min-height: 0;
}

.image-container {
  width: 100%;
  height: 100%;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  overflow: auto;
  overflow-x: scroll;
  overflow-y: scroll;
  background: #1a1a2e;
  background-image:
    linear-gradient(45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(-45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #2a2a3e 75%),
    linear-gradient(-45deg, transparent 75%, #2a2a3e 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  position: relative;
  user-select: none;
  display: block;
  flex-shrink: 0;
}

/* 确保滚动条可见 */
.image-container::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

.image-container::-webkit-scrollbar-track {
  background: rgba(26, 26, 46, 0.5);
  border-radius: 6px;
}

.image-container::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.5);
  border-radius: 6px;
  border: 2px solid rgba(26, 26, 46, 0.5);
}

.image-container::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.8);
}

.image-container::-webkit-scrollbar-corner {
  background: rgba(26, 26, 46, 0.5);
}

.preview-image {
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  display: block;
  pointer-events: auto;
  cursor: crosshair;
  margin: 0 auto;
}

.action-btn {
  width: 100%;
  padding: 12px;
  font-size: 14px;
  margin-bottom: 12px;
}

.action-btn:last-child {
  margin-bottom: 0;
}

.zoom-btn {
  margin-top: 8px;
}

.zoom-info {
  margin-top: 12px;
  padding: 8px;
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(51, 65, 85, 0.3);
  border-radius: 4px;
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

.empty-preview {
  width: 100%;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 确保弹框内容区域固定高度 */
:deep(.selection-dialog .el-dialog__body) {
  padding: 20px;
  overflow: hidden;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .selection-dialog-layout {
    grid-template-columns: 1fr;
    height: auto;
    min-height: 600px;
  }
}
</style>
