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
            type="success"
            :icon="VideoPlay"
            size="small"
            :loading="processing"
            :disabled="!imageLoaded || pipeline.length === 0"
            @click="startProcessing"
          >
            开始处理
          </el-button>
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
              <el-dropdown-menu>
                <el-dropdown-item command="color_filter">
                  <el-icon><Brush /></el-icon> 颜色过滤
                </el-dropdown-item>
                <el-dropdown-item command="binary">
                  <el-icon><MagicStick /></el-icon> 二值化
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
              :is-selecting-point="false"
              :get-color-preview="getColorPreview"
              @update:params="updateStepParams(step.id, $event)"
              @toggle-expand="toggleStepExpand(step.id)"
              @remove="removeStep(index)"
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

      <!-- 洪水填充区域 -->
      <div class="flood-fill-section">
        <div class="flood-fill-toolbar">
          <div class="toolbar-left">
            <el-icon class="pipeline-icon flood-fill-icon"><Aim /></el-icon>
            <span class="pipeline-title">洪水填充</span>
          </div>
        </div>
        <div class="flood-fill-body">
          <!-- 图片来源选择 -->
          <div class="param-row">
            <span class="param-label">填充来源</span>
            <el-radio-group v-model="floodFillSource" size="small">
              <el-radio-button value="processed">管线结果</el-radio-button>
              <el-radio-button value="stitched">拼接结果</el-radio-button>
            </el-radio-group>
          </div>
          <!-- 坐标 -->
          <div class="flood-coord-row">
            <span class="param-label">X:</span>
            <el-input-number v-model="floodFillX" :min="0" size="small" controls-position="right" />
            <span class="param-label">Y:</span>
            <el-input-number v-model="floodFillY" :min="0" size="small" controls-position="right" />
            <el-button
              type="primary" size="small"
              :class="{ 'is-selecting': isSelectingFloodFillPoint }"
              :disabled="(floodFillSource === 'processed' && !processedImage) || (floodFillSource === 'stitched' && !stitchedImage)"
              @click="startFloodFillPointSelection"
            >
              <el-icon><Aim /></el-icon>
              <span>{{ isSelectingFloodFillPoint ? '点击图片...' : '拾取' }}</span>
            </el-button>
          </div>
          <!-- 操作按钮 -->
          <div class="flood-fill-actions">
            <el-button
              type="success" size="small"
              :icon="VideoPlay"
              :loading="floodFillProcessing"
              :disabled="(floodFillSource === 'processed' && !processedImage) || (floodFillSource === 'stitched' && !stitchedImage)"
              @click="executeFloodFill"
            >
              执行填充
            </el-button>
            <el-button
              size="small"
              :icon="Film"
              :disabled="(floodFillSource === 'processed' && !processedImage) || (floodFillSource === 'stitched' && !stitchedImage)"
              @click="showFloodFillAnimation"
            >
              查看动画
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
          管线处理结果
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
        <div
          class="preview-mode-tab"
          :class="{ active: previewMode === 'flood-fill' }"
          @click="previewMode = 'flood-fill'"
        >
          洪水填充
          <el-tag v-if="floodFillResult" size="small" type="warning" effect="dark" style="margin-left: 6px;">
            ✓
          </el-tag>
        </div>
        <div class="preview-bar-right">
          <div v-if="isAutoStitching" class="auto-stitch-indicator">
            <span class="auto-stitch-dot"></span>
            连续拼接中...
          </div>
          <el-button
            v-if="displayImage"
            type="primary"
            size="small"
            :icon="Download"
            @click="handleSaveCurrentPreview"
          >
            保存图片
          </el-button>
        </div>
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
          <p v-else-if="previewMode === 'flood-fill'">洪水填充结果将显示在这里</p>
          <p v-else>处理后的图片将显示在这里</p>
          <p class="hint" v-if="previewMode === 'stitched'">点击「拼接一次」或「连续拼接」开始</p>
          <p class="hint" v-else-if="previewMode === 'flood-fill'">选择来源图片并执行填充</p>
          <p class="hint" v-else>上传图片并添加处理步骤</p>
        </div>
        <div v-else class="preview-image-wrapper" :style="previewWrapperStyle">
          <img
            :src="displayImage"
            :alt="previewMode === 'stitched' ? '拼接结果' : previewMode === 'flood-fill' ? '洪水填充结果' : '处理结果'"
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
  Upload, CircleClose, Film,
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

  // 独立洪水填充
  floodFillSource,
  floodFillX,
  floodFillY,
  floodFillResult,
  floodFillProcessing,
  isSelectingFloodFillPoint,

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
  handleSaveImage,
  handleDragStart,
  handleDragOver,
  handleDrop,
  handleDragEnd,
  startProcessing,

  // 独立洪水填充方法
  startFloodFillPointSelection,
  handleFloodFillImageClick,
  executeFloodFill,
  showFloodFillAnimation,

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
  handleSaveProcessedImage,
  handleSaveFloodFillImage,

  initSocket,
  initIpcListeners,
  cleanup,
} = useColoring();

const displayImage = computed(() => {
  if (previewMode.value === 'stitched' && stitchedImage.value) {
    return stitchedImage.value;
  }
  if (previewMode.value === 'flood-fill' && floodFillResult.value) {
    return floodFillResult.value;
  }
  return processedImage.value;
});

function handleSaveCurrentPreview() {
  if (previewMode.value === 'stitched') {
    handleSaveStitchedImage();
  } else if (previewMode.value === 'flood-fill') {
    handleSaveFloodFillImage();
  } else {
    handleSaveProcessedImage();
  }
}

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
  if (isSelectingFloodFillPoint.value) return 'crosshair';
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
  if (!isSelectingFloodFillPoint.value) return;
  if (!previewImageRef.value || !previewContainerRef.value) return;

  const containerRect = previewContainerRef.value.getBoundingClientRect();
  const containerX = event.clientX - containerRect.left;
  const containerY = event.clientY - containerRect.top;
  const imageX = containerX - previewTranslateX.value;
  const imageY = containerY - previewTranslateY.value;
  const actualX = Math.round(imageX / previewScale.value);
  const actualY = Math.round(imageY / previewScale.value);

  handleFloodFillImageClick(actualX, actualY);
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

<style scoped lang="less">
@primary: #6366f1;
@primary-light: #818cf8;
@success: #10b981;
@warning: #f59e0b;
@danger: #ef4444;
@bg-main: #eef0f4;
@bg-card: #ffffff;
@text-primary: #1e293b;
@text-secondary: #64748b;
@text-muted: #94a3b8;
@border: #e2e8f0;
@border-strong: #cbd5e1;
@shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
@shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.06);

.coloring-root {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: @bg-main;
}

.coloring-layout {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 380px;
  min-width: 380px;
  max-width: 380px;
  height: 100%;
  padding: 8px;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
}

/* ===== 通用 section 样式 ===== */
.pipeline-section,
.stitch-section,
.flood-fill-section {
  display: flex;
  flex-direction: column;
  background: @bg-card;
  border-radius: 10px;
  border: 1px solid @border;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: @shadow-sm;
}

.pipeline-section {
  flex: 1;
  min-height: 180px;
  flex-shrink: 1;
}

.pipeline-toolbar,
.stitch-toolbar,
.flood-fill-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid @border;
  gap: 6px;
  flex-wrap: wrap;
}

.pipeline-toolbar {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.04) 0%, rgba(99, 102, 241, 0.08) 100%);
}

.stitch-toolbar {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.04) 0%, rgba(16, 185, 129, 0.08) 100%);
}

.flood-fill-toolbar {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.04) 0%, rgba(245, 158, 11, 0.08) 100%);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pipeline-icon {
  font-size: 16px;
  color: @primary;
}

.flood-fill-icon {
  color: @warning !important;
}

.pipeline-title {
  font-size: 13px;
  font-weight: 600;
  color: @text-primary;
}

.pipeline-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.empty-pipeline {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  color: @text-muted;
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 10px;
  opacity: 0.3;
}

.empty-pipeline p {
  margin: 0;
  text-align: center;
  font-size: 13px;
}

.empty-pipeline .hint {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.6;
}

/* ===== 拼接控制 ===== */
.stitch-body,
.flood-fill-body {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

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
  max-height: 90px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 8px;
  background: #f8fafc;
  border: 1px solid @border;
  border-radius: 6px;
}

.batch-file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 11px;
  color: @text-secondary;
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
  color: @text-muted;
  cursor: pointer;
  flex-shrink: 0;
  transition: color 0.2s;
}

.batch-file-remove:hover {
  color: @danger;
}

.batch-empty-hint {
  font-size: 11px;
  color: @text-muted;
  text-align: center;
  padding: 8px;
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
  color: @text-secondary;
  white-space: nowrap;
  min-width: 56px;
}

.param-row :deep(.el-input-number) {
  width: 130px;
}

.stitch-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: #f0fdf4;
  border: 1px solid rgba(16, 185, 129, 0.15);
  border-radius: 6px;
  font-size: 12px;
  color: @text-secondary;
}

.conf-good { color: @success; }
.conf-warn { color: @warning; }

.stitch-actions {
  display: flex;
  gap: 6px;
}

.stitch-actions .el-button {
  flex: 1;
}

/* ===== 洪水填充 ===== */
.flood-coord-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.flood-coord-row :deep(.el-input-number) {
  width: 90px;
}

.flood-fill-actions {
  display: flex;
  gap: 6px;
}

.flood-fill-actions .el-button {
  flex: 1;
}

.is-selecting {
  animation: pulse-selecting 1.2s infinite;
}

@keyframes pulse-selecting {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.3); }
  50% { box-shadow: 0 0 0 5px rgba(99, 102, 241, 0); }
}

/* ===== 右侧预览 ===== */
.image-preview-panel-wrapper {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: @bg-card;
  border-left: 1px solid @border;
}

.preview-mode-bar {
  display: flex;
  align-items: center;
  padding: 0 12px;
  background: @bg-card;
  border-bottom: 1px solid @border;
  flex-shrink: 0;
  height: 38px;
  gap: 0;
}

.preview-mode-tab {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  font-size: 12px;
  color: @text-muted;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  user-select: none;
  margin-bottom: -1px;
  font-weight: 500;
}

.preview-mode-tab:hover {
  color: @text-primary;
  background: rgba(99, 102, 241, 0.03);
}

.preview-mode-tab.active {
  color: @primary;
  border-bottom-color: @primary;
  font-weight: 600;
}

.preview-bar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.auto-stitch-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: @success;
  font-weight: 500;
  padding: 3px 10px;
  background: rgba(16, 185, 129, 0.06);
  border-radius: 12px;
  animation: pulse-opacity 1.5s ease-in-out infinite;
}

.auto-stitch-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: @success;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
}

@keyframes pulse-opacity {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.image-preview-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  position: relative;
  user-select: none;
  box-sizing: border-box;
  background-color: #f1f5f9;
  background-image:
    linear-gradient(45deg, #e2e8f0 25%, transparent 25%),
    linear-gradient(-45deg, #e2e8f0 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #e2e8f0 75%),
    linear-gradient(-45deg, transparent 75%, #e2e8f0 75%);
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
  color: @text-muted;
  text-align: center;
  gap: 4px;
}

.preview-empty-icon {
  font-size: 48px;
  margin-bottom: 10px;
  opacity: 0.25;
  color: @border-strong;
}

.preview-empty p {
  margin: 0;
  font-size: 13px;
  color: @text-secondary;
}

.preview-empty .hint {
  font-size: 11px;
  color: @text-muted;
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

/* TransitionGroup */
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.25s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-leave-active {
  position: absolute;
}
</style>
