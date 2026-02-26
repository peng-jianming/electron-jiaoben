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
        :current-device-id="currentDeviceId"
        :device-tab="deviceTab"
        :screenshot-loading="screenshotLoading"
        :capture-window-loading="captureWindowLoading"
        @image-select="handleImageSelect"
        @open-device-dialog="openDeviceDialog"
        @capture-screenshot="handleCaptureScreenshot"
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
          <el-button
          type="danger"
          :icon="Delete"
          size="small" 
          @click="clearAllSteps"
          :disabled="processing || pipeline.length === 0"
        >
          清空
        </el-button>
          <el-dropdown trigger="click" @command="addStep">
            <el-button type="primary" size="small" :icon="Plus">
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

      <!-- 拼接控制区域 -->
      <div class="stitch-section">
        <div class="stitch-toolbar">
          <div class="toolbar-left">
            <el-icon class="pipeline-icon"><Connection /></el-icon>
            <span class="pipeline-title">拼接控制</span>
            <el-tag v-if="stitchCount > 0" size="small" type="success" effect="dark">
              {{ stitchCount }} 张
            </el-tag>
          </div>
        </div>
        <div class="stitch-body">
          <!-- 批量图片上传区（用于"拼接一次"） -->
          <div class="batch-upload-area">
            <div class="batch-upload-header">
              <span class="param-label">批量图片</span>
              <div class="batch-upload-btns">
                <el-upload
                  :auto-upload="false"
                  :show-file-list="false"
                  :on-change="(file) => addStitchFiles(file)"
                  accept="image/*"
                  multiple
                >
                  <el-button size="small" :icon="Upload" :disabled="batchStitching">选择图片</el-button>
                </el-upload>
                <el-button
                  v-if="stitchBatchFiles.length > 0"
                  size="small"
                  text
                  type="danger"
                  @click="clearStitchFiles"
                  :disabled="batchStitching"
                >清空</el-button>
              </div>
            </div>
            <div v-if="stitchBatchFiles.length > 0" class="batch-file-list">
              <div
                v-for="(file, idx) in stitchBatchFiles"
                :key="idx"
                class="batch-file-item"
              >
                <span class="batch-file-name" :title="file.name">{{ idx + 1 }}. {{ file.name }}</span>
                <el-icon
                  class="batch-file-remove"
                  @click="removeStitchFile(idx)"
                  v-if="!batchStitching"
                ><CircleClose /></el-icon>
              </div>
            </div>
            <div v-else class="batch-empty-hint">选择多张图片后点击「拼接一次」</div>
          </div>

          <!-- 拼接参数 -->
          <div class="stitch-params">
            <div class="param-row">
              <span class="param-label">水平搜索</span>
              <el-input-number v-model="stitchMaxDx" :min="50" :max="1000" :step="50" size="small" controls-position="right" />
            </div>
            <div class="param-row">
              <span class="param-label">垂直搜索</span>
              <el-input-number v-model="stitchMaxDy" :min="50" :max="1000" :step="50" size="small" controls-position="right" />
            </div>
            <div class="param-row">
              <span class="param-label">间隔(ms)</span>
              <el-input-number v-model="stitchInterval" :min="100" :max="5000" :step="100" size="small" controls-position="right" />
            </div>
          </div>
          <!-- 状态信息 -->
          <div v-if="stitchCount > 0" class="stitch-status">
            <span>已拼接: <strong>{{ stitchCount }}</strong> 张</span>
            <span v-if="lastStitchConfidence > 0">
              置信度: <strong :class="lastStitchConfidence >= 0.5 ? 'conf-good' : 'conf-warn'">
                {{ (lastStitchConfidence * 100).toFixed(1) }}%
              </strong>
            </span>
          </div>
          <!-- 操作按钮 -->
          <div class="stitch-actions">
            <el-button
              size="small"
              type="primary"
              :icon="Connection"
              :loading="batchStitching"
              :disabled="isAutoStitching || stitchBatchFiles.length === 0"
              @click="doBatchStitch"
            >
              拼接一次 ({{ stitchBatchFiles.length }})
            </el-button>
            <el-button
              v-if="!isAutoStitching"
              size="small"
              type="success"
              :icon="VideoPlay"
              :disabled="batchStitching"
              @click="startAutoStitch"
            >
              连续拼接
            </el-button>
            <el-button
              v-else
              size="small"
              type="warning"
              :icon="VideoPause"
              @click="stopAutoStitch"
            >
              停止拼接
            </el-button>
          </div>
          <div class="stitch-actions">
            <el-button
              size="small"
              :icon="RefreshLeft"
              :disabled="stitchCount === 0 || isAutoStitching || batchStitching"
              @click="clearStitch"
            >
              清空拼接
            </el-button>
            <el-button
              size="small"
              type="success"
              :icon="Download"
              :disabled="!stitchedImage"
              @click="handleSaveStitchedImage"
            >
              保存拼接图
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧图片预览区域 -->
    <div class="image-preview-panel-wrapper">
      <!-- 预览模式切换 -->
      <div class="preview-mode-bar">
        <div
          class="preview-mode-tab"
          :class="{ active: previewMode === 'processed' }"
          @click="previewMode = 'processed'"
        >
          处理结果
        </div>
        <div
          class="preview-mode-tab"
          :class="{ active: previewMode === 'stitched' }"
          @click="previewMode = 'stitched'"
        >
          拼接结果
          <el-tag v-if="stitchCount > 0" size="small" type="success" effect="dark" style="margin-left: 6px;">
            {{ stitchCount }}
          </el-tag>
        </div>
        <div v-if="isAutoStitching" class="auto-stitch-indicator">
          <span class="auto-stitch-dot"></span>
          连续拼接中...
        </div>
        <el-button
          type="success"
          :icon="Download"
          @click="handleSaveImage"
          :disabled="processing"
        >
          保存图片
        </el-button>
      </div>
      <div class="image-preview-panel"
           ref="previewContainerRef"
           :style="{ cursor: previewCursor }"
           @wheel="handlePreviewWheel"
           @mousedown="handlePreviewMouseDown"
           @mousemove="handlePreviewMouseMove"
           @mouseup="handlePreviewMouseUp"
           @click="handlePreviewClick"
      >
        <div v-if="!displayImage" class="preview-empty">
          <el-icon class="preview-empty-icon"><Picture /></el-icon>
          <p v-if="previewMode === 'stitched'">拼接结果将显示在这里</p>
          <p v-else>处理后的图片将显示在这里</p>
          <p class="hint" v-if="previewMode === 'stitched'">点击「拼接一次」或「连续拼接」开始</p>
          <p class="hint" v-else>上传图片并添加处理步骤</p>
        </div>
        <div v-else class="preview-image-wrapper" :style="previewWrapperStyle">
          <img
            :src="displayImage"
            :alt="previewMode === 'stitched' ? '拼接结果' : '处理结果'"
            ref="previewImageRef"
            :style="previewImageStyle"
            @load="handlePreviewImageLoad"
            draggable="false"
          />
        </div>
      </div>
    </div>

    <!-- 设备连接弹框（与 ImageProcessor 共用组件） -->
    <ImageProcessorDeviceDialog
      v-model:visible="deviceDialogVisible"
      v-model:tab="deviceTab"
      :device-list="deviceList"
      :device-loading="deviceLoading"
      :selected-device-id="selectedDeviceId"
      :current-device-id="currentDeviceId"
      @update:selected-device-id="(val) => (selectedDeviceId = val)"
      @refresh-devices="refreshDevices"
      @connect-selected-device="connectSelectedDevice"
      @open-capture-window="openCaptureWindow"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import {
  List, Plus, Delete, Download, DocumentAdd,
  Brush, MagicStick, Aim, Picture,
  Connection, VideoPause, VideoPlay, RefreshLeft,
  Upload, CircleClose,
} from '@element-plus/icons-vue';
import { useColoring } from '../../composables/useColoring';
import ImageUploadCard from './cards/ImageUploadCard.vue';
import PipelineStepCard from './cards/PipelineStepCard.vue';
import ImageProcessorDeviceDialog from '../ImageProcessor/dialogs/ImageProcessorDeviceDialog.vue';

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

  deviceDialogVisible,
  deviceList,
  deviceLoading,
  selectedDeviceId,
  currentDeviceId,
  screenshotLoading,
  captureWindowLoading,
  deviceTab,

  stitchedImage,
  stitchCount,
  isAutoStitching,
  stitchLoading,
  lastStitchConfidence,
  stitchMaxDx,
  stitchMaxDy,
  stitchInterval,
  previewMode,

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

  openDeviceDialog,
  refreshDevices,
  connectSelectedDevice,
  captureScreenshot,
  openCaptureWindow,
  captureWindowScreenshot,

  stitchBatchFiles,
  batchStitching,
  addStitchFiles,
  removeStitchFile,
  clearStitchFiles,
  doBatchStitch,
  startAutoStitch,
  stopAutoStitch,
  clearStitch,
  handleSaveStitchedImage,

  initSocket,
  initIpcListeners,
  cleanup,
} = useColoring();

const displayImage = computed(() => {
  if (previewMode.value === 'stitched' && stitchedImage.value) {
    return stitchedImage.value;
  }
  return processedImage.value;
});

function handleCaptureScreenshot() {
  if (deviceTab.value === "capture-window") {
    captureWindowScreenshot();
  } else {
    captureScreenshot();
  }
}

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
  if (!displayImage.value || !previewImageRef.value || !previewContainerRef.value) return;
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
  if (!displayImage.value || event.button !== 0) return;
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

/* ===== 拼接控制区域 ===== */
.stitch-section {
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  flex-shrink: 0;
}

.stitch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: rgba(16, 185, 129, 0.1);
  border-bottom: 1px solid var(--border-color);
}

.stitch-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 批量图片上传 */
.batch-upload-area {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.batch-upload-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.batch-upload-btns {
  display: flex;
  align-items: center;
  gap: 4px;
}

.batch-file-list {
  max-height: 100px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 8px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 6px;
}

.batch-file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 11px;
  color: var(--text-secondary);
  padding: 2px 0;
}

.batch-file-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.batch-file-remove {
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  opacity: 0.6;
  transition: all 0.2s;
}

.batch-file-remove:hover {
  color: #ef4444;
  opacity: 1;
}

.batch-empty-hint {
  font-size: 11px;
  color: var(--text-secondary);
  opacity: 0.6;
  text-align: center;
  padding: 6px;
}

.stitch-params {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.param-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.param-label {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  min-width: 64px;
}

.param-row .el-input-number {
  width: 140px;
}

.stitch-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.conf-good {
  color: #10b981;
}

.conf-warn {
  color: #f59e0b;
}

.stitch-actions {
  display: flex;
  gap: 8px;
}

.stitch-actions .el-button {
  flex: 1;
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
.image-preview-panel-wrapper {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--border-color);
}

.preview-mode-bar {
  display: flex;
  align-items: center;
  padding: 0 12px;
  /* background: rgba(30, 30, 46, 0.95); */
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  height: 36px;
  gap: 2px;
}

.preview-mode-tab {
  display: flex;
  align-items: center;
  padding: 6px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  user-select: none;
}

.preview-mode-tab:hover {
  color: var(--text-primary);
}

.preview-mode-tab.active {
  color: var(--primary-light);
  border-bottom-color: var(--primary-color);
  font-weight: 600;
}

.auto-stitch-indicator {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #10b981;
  animation: pulse-opacity 1.5s ease-in-out infinite;
}

.auto-stitch-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

@keyframes pulse-opacity {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.image-preview-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  background: #1a1a2e;
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
