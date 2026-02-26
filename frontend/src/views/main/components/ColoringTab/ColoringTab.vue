<template>

<!-- 这个组件是为了得到二值化参数,也就是需要通过一系列操作例如颜色过滤,二值化,膨胀,腐蚀,得到二值化参数 -->
<!-- 这个组件只是二值化大地图或者小地图的组件,如果是小地图则将所有小地图二值化后进行拼接,如果是大地图则直接二值化 -->
<!-- 这个组件最终结果得到一张洪水填充后的大地图和一系列参数 -->

<!-- 通过小地图(参考)or直接有大地图,制作二值化大地图(需要和参考地图对应上大小,可以通过缩放等方式) -->
<!-- 通过小地图(参考)跟大地图进行模板匹配,知道角色目前在大地图的什么位置 -->
<!-- 大地图进行路线规划,然后控制角色按照路线规划走 -->
  <div class="coloring-root">
    <!-- 左侧控制面板 -->
    <div class="coloring-layout">
      <!-- 图像上传区 -->
      <ImageUploadCard
        :image-file-name="imageFileName"
        :original-image-url="originalImageUrl"
        @image-select="handleImageSelect"
      />

      <!-- 管线区域 -->
      <div class="pipeline-section">
        <!-- 管线头部：标题 + 添加步骤 -->
        <div class="pipeline-toolbar">
          <div class="toolbar-left">
            <el-icon class="pipeline-icon"><List /></el-icon>
            <span class="pipeline-title">处理管线</span>
            <el-tag size="small" type="info" effect="dark">{{ pipeline.length }} 步</el-tag>
          </div>
          <el-dropdown trigger="click" @command="addStep" :disabled="!imageLoaded">
            <el-button type="primary" size="small" :icon="Plus" :disabled="!imageLoaded">
              添加步骤
            </el-button>
            <template #dropdown>
            <!-- 颜色过滤,二值化,膨胀, 腐蚀,洪水填充 -->
              <el-dropdown-menu>
                <el-dropdown-item command="color_filter">
                  <el-icon><Brush /></el-icon> 颜色过滤
                </el-dropdown-item>
                <el-dropdown-item command="binary">
                  <el-icon><MagicStick /></el-icon> 二值化
                </el-dropdown-item>
                <el-dropdown-item command="flood_fill">
                  <el-icon><Aim /></el-icon> 洪水填充
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <!-- 步骤列表 -->
        <div class="pipeline-list" v-if="pipeline.length > 0">
          <TransitionGroup name="list">
            <PipelineStepCard
              v-for="(step, index) in pipeline"
              :key="step.id"
              :step="step"
              :index="index"
              :is-dragging="dragIndex === index"
              :is-selecting-point="activeFloodFillStepId === step.id"
              :get-color-preview="getColorPreview"
              @update:params="updateStepParams(step.id, $event)"
              @toggle-expand="toggleStepExpand(step.id)"
              @remove="removeStep(index)"
              @show-animation="showFloodFillAnimation(index, step)"
              @select-point="startPointSelection(step.id)"
              @drag-start="handleDragStart"
              @drag-over="handleDragOver"
              @drag-end="handleDragEnd"
              @drop="handleDrop"
            />
          </TransitionGroup>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-pipeline">
          <el-icon class="empty-icon"><DocumentAdd /></el-icon>
          <p>暂无处理步骤</p>
          <p class="hint">点击上方「添加步骤」来构建处理管线</p>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="action-bar" v-if="imageLoaded">
        <el-button
          type="danger"
          :icon="Delete"
          @click="clearAllSteps"
          :disabled="processing || pipeline.length === 0"
        >
          清空
        </el-button>
        <el-button
          type="success"
          :icon="Download"
          @click="handleSaveImage"
          :disabled="processing"
        >
          保存图片
        </el-button>
      </div>
    </div>

    <!-- 右侧图片预览区域 -->
    <div class="image-preview-panel"
         ref="previewContainerRef"
         :style="{ cursor: previewCursor }"
         @wheel="handlePreviewWheel"
         @mousedown="handlePreviewMouseDown"
         @mousemove="handlePreviewMouseMove"
         @mouseup="handlePreviewMouseUp"
         @click="handlePreviewClick"
    >
      <div v-if="!processedImage" class="preview-empty">
        <el-icon class="preview-empty-icon"><Picture /></el-icon>
        <p>处理后的图片将显示在这里</p>
        <p class="hint">上传图片并添加处理步骤</p>
      </div>
      <div v-else class="preview-image-wrapper" :style="previewWrapperStyle">
        <img
          :src="processedImage"
          alt="处理结果"
          ref="previewImageRef"
          :style="previewImageStyle"
          @load="handlePreviewImageLoad"
          draggable="false"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import {
  List, Plus, Delete, Download, DocumentAdd,
  Brush, MagicStick, Aim, Picture,
} from '@element-plus/icons-vue';
import { useColoring } from '../../composables/useColoring';
import ImageUploadCard from './cards/ImageUploadCard.vue';
import PipelineStepCard from './cards/PipelineStepCard.vue';

const previewContainerRef = ref(null);
const previewImageRef = ref(null);

const {
  imageFileName,
  originalImageUrl,
  processing,
  imageLoaded,
  processedImage,
  pipeline,
  dragIndex,
  activeFloodFillStepId,

  getColorPreview,
  addStep,
  updateStepParams,
  toggleStepExpand,
  removeStep,
  clearAllSteps,
  handleImageSelect,
  handleImageClick,
  handleSaveImage,
  startPointSelection,
  showFloodFillAnimation,
  handleDragStart,
  handleDragOver,
  handleDrop,
  handleDragEnd,

  initSocket,
  initIpcListeners,
  cleanup,
} = useColoring();

// ==================== Preview Zoom/Pan ====================

const previewScale = ref(1);
const previewTranslateX = ref(0);
const previewTranslateY = ref(0);
const previewIsDragging = ref(false);
let previewDragStartX = 0;
let previewDragStartY = 0;
let previewDragStartTranslateX = 0;
let previewDragStartTranslateY = 0;
let previewSuppressClick = false;

const previewWrapperStyle = computed(() => ({
  transform: `translate(${previewTranslateX.value}px, ${previewTranslateY.value}px)`,
  position: 'absolute',
  top: 0,
  left: 0,
}));

const previewImageStyle = computed(() => ({
  transform: `scale(${previewScale.value})`,
  transformOrigin: 'top left',
  display: 'block',
}));

const previewCursor = computed(() => {
  if (activeFloodFillStepId.value) return 'crosshair';
  if (previewIsDragging.value) return 'grabbing';
  return 'default';
});

function handlePreviewImageLoad() {
  nextTick(() => {
    calculatePreviewTransform();
  });
}

function calculatePreviewTransform() {
  if (!previewImageRef.value || !previewContainerRef.value) return;
  const containerRect = previewContainerRef.value.getBoundingClientRect();
  const imgWidth = previewImageRef.value.naturalWidth;
  const imgHeight = previewImageRef.value.naturalHeight;

  const scaleX = containerRect.width / imgWidth;
  const scaleY = containerRect.height / imgHeight;
  const scale = Math.min(scaleX, scaleY, 1);

  previewScale.value = scale;
  const scaledWidth = imgWidth * scale;
  const scaledHeight = imgHeight * scale;
  previewTranslateX.value = (containerRect.width - scaledWidth) / 2;
  previewTranslateY.value = (containerRect.height - scaledHeight) / 2;
}

function handlePreviewWheel(event) {
  if (!processedImage.value || !previewImageRef.value || !previewContainerRef.value) return;
  if (!event.ctrlKey && !event.metaKey) return;

  event.preventDefault();
  const containerRect = previewContainerRef.value.getBoundingClientRect();
  const mouseX = event.clientX - containerRect.left;
  const mouseY = event.clientY - containerRect.top;

  const imgX = (mouseX - previewTranslateX.value) / previewScale.value;
  const imgY = (mouseY - previewTranslateY.value) / previewScale.value;

  const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(0.1, Math.min(10, previewScale.value * zoomFactor));

  previewTranslateX.value = mouseX - imgX * newScale;
  previewTranslateY.value = mouseY - imgY * newScale;
  previewScale.value = newScale;
}

function handlePreviewMouseDown(event) {
  if (!processedImage.value || event.button !== 0) return;
  previewIsDragging.value = true;
  previewDragStartX = event.clientX;
  previewDragStartY = event.clientY;
  previewDragStartTranslateX = previewTranslateX.value;
  previewDragStartTranslateY = previewTranslateY.value;
  event.preventDefault();
}

function handlePreviewMouseMove(event) {
  if (!previewIsDragging.value) return;
  const deltaX = event.clientX - previewDragStartX;
  const deltaY = event.clientY - previewDragStartY;
  previewTranslateX.value = previewDragStartTranslateX + deltaX;
  previewTranslateY.value = previewDragStartTranslateY + deltaY;
}

function handlePreviewMouseUp(event) {
  if (previewIsDragging.value) {
    const dx = Math.abs(event.clientX - previewDragStartX);
    const dy = Math.abs(event.clientY - previewDragStartY);
    if (dx > 3 || dy > 3) {
      previewSuppressClick = true;
    }
    previewIsDragging.value = false;
  }
}

function handlePreviewClick(event) {
  if (previewSuppressClick) {
    previewSuppressClick = false;
    return;
  }
  if (!activeFloodFillStepId.value) return;
  if (!previewImageRef.value || !previewContainerRef.value) return;

  const containerRect = previewContainerRef.value.getBoundingClientRect();
  const containerX = event.clientX - containerRect.left;
  const containerY = event.clientY - containerRect.top;
  const imageX = containerX - previewTranslateX.value;
  const imageY = containerY - previewTranslateY.value;
  const actualX = Math.round(imageX / previewScale.value);
  const actualY = Math.round(imageY / previewScale.value);

  handleImageClick(actualX, actualY);
}

function handleGlobalPreviewMouseUp() {
  if (previewIsDragging.value) {
    previewIsDragging.value = false;
  }
}

defineExpose({
  handleSaveImage,
  processing,
  imageLoaded,
});

onMounted(() => {
  initSocket();
  initIpcListeners();
  document.addEventListener('mouseup', handleGlobalPreviewMouseUp);
});

onUnmounted(() => {
  cleanup();
  document.removeEventListener('mouseup', handleGlobalPreviewMouseUp);
});
</script>

<style scoped>
.coloring-root {
  display: flex;
  width: 100%;
  height: 100%;
  gap: 0;
  overflow: hidden;
  box-sizing: border-box;
}

.coloring-layout {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 420px;
  min-width: 420px;
  max-width: 420px;
  height: 100%;
  padding: 8px;
  overflow: hidden;
  box-sizing: border-box;
}

/* ===== 管线区域 ===== */
.pipeline-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.pipeline-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(51, 65, 85, 0.3);
  border-bottom: 1px solid var(--border-color);
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pipeline-icon {
  font-size: 18px;
  color: var(--primary-light);
}
.pipeline-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.pipeline-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 空状态 */
.empty-pipeline {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.4;
}
.empty-pipeline p { margin: 0; text-align: center; }
.empty-pipeline .hint {
  font-size: 12px;
  margin-top: 8px;
  opacity: 0.7;
}

/* ===== 底部操作栏 ===== */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}
/* ===== 右侧图片预览区域 ===== */
.image-preview-panel {
  flex: 1;
  min-width: 0;
  height: 100%;
  background: #1a1a2e;
  border-left: 1px solid var(--border-color);
  overflow: hidden;
  position: relative;
  user-select: none;
  box-sizing: border-box;
  background-image:
    linear-gradient(45deg, #1e1e3a 25%, transparent 25%),
    linear-gradient(-45deg, #1e1e3a 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #1e1e3a 75%),
    linear-gradient(-45deg, transparent 75%, #1e1e3a 75%);
  background-size: 16px 16px;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
}

.preview-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #64748b;
  text-align: center;
  gap: 4px;
}
.preview-empty-icon {
  font-size: 64px;
  margin-bottom: 12px;
  opacity: 0.3;
}
.preview-empty p {
  margin: 0;
  font-size: 14px;
}
.preview-empty .hint {
  font-size: 12px;
  opacity: 0.6;
}

.preview-image-wrapper {
  display: inline-block;
  position: relative;
  user-select: none;
}

.preview-image-wrapper img {
  display: block;
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  user-select: none;
  pointer-events: none;
  border-radius: 0;
}

/* TransitionGroup 动画 */
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
.list-leave-active {
  position: absolute;
}
</style>
