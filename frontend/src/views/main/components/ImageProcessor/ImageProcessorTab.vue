<template>
  <div class="image-processor-tab">
    <!-- 左中右布局 -->
    <div class="processor-layout">
      <!-- 左侧：功能按钮区域 -->
      <div class="left-panel">
        <ImageProcessorLeftPanel
          :current-device-id="currentDeviceId"
          :device-tab="deviceTab"
          :screenshot-loading="screenshotLoading"
          :capture-window-loading="captureWindowLoading"
          :selection-enabled="selectionEnabled"
          :selectionInfo="selectionInfo"
          :has-image="!!currentImage"
          @load-image="handleLoadImage"
          @open-device-dialog="openDeviceDialog"
          @capture-screenshot="handleCaptureScreenshot"
          @toggle-selection="toggleSelectionMode"
          @fit-to-window="fitToWindow"
          @reset-zoom="resetZoom"
          @save-image="handleSaveImage"
          @crop-image="handleCropImage"
          @copy-selection="handleCopySelection"
        />
        <!-- 隐藏的文件选择框，供“载入图片”按钮触发 -->
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          multiple
          style="display: none"
          @change="handleFileSelect"
        />
      </div>

      <!-- 中间：图片显示区域 -->
      <div class="center-panel">
        <el-tabs
          v-if="images.length >= 1"
          v-model="currentImageIndex"
          type="border-card"
          closable
          @tab-remove="removeImage"
        >
          <el-tab-pane
            v-for="(image, index) in images"
            :key="index"
            :label="image.name"
            :name="String(index)"
          >
          </el-tab-pane>
        </el-tabs>
        <div
          class="image-container"
          ref="imageContainerRef"
          :style="{ cursor: isDragging ? 'grabbing' : (isSpacePressed ? 'grab' : containerCursor) }"
          @mousemove="handleContainerMouseMove"
          @mouseenter="handleMouseEnter"
          @mouseleave="handleMouseLeave"
          @mousedown="handleMouseDown"
          @mouseup="handleMouseUp"
          @contextmenu.prevent="handleRightClick"
          @click="handleImageClick"
          @wheel="handleWheel"
        >
          <div v-if="currentImage" class="image-wrapper" :style="imageWrapperStyle">
            <img
              :src="currentImage.url"
              alt="预览图片"
              ref="imageRef"
              @load="handleImageLoad"
              draggable="false"
              :style="imageStyle"
            />
            <!-- 圈选矩形高亮 -->
            <div
              v-if="selectionDisplay"
              class="selection-rect"
              :style="selectionStyle"
            ></div>
            <!-- 代码生成器圈选矩形高亮 -->
            <div
              v-if="codeGeneratorSelectionDisplay"
              class="code-generator-selection-rect"
              :style="codeGeneratorSelectionStyle"
            ></div>
          </div>
          <div v-else class="empty-placeholder">
            <el-icon class="empty-icon"><Picture /></el-icon>
            <p>请载入图片</p>
          </div>
        </div>
      </div>

      <!-- 右侧：放大镜和颜色信息 -->
      <div class="right-panel">
        <ImageProcessorRightPanel
          :magnifier-visible="magnifierVisible"
          :current-image="currentImage"
          :current-position="currentPosition"
          :current-color="currentColor"
          :current-selected-colors="currentSelectedColors"
          :recorded-colors="recordedColors"
          :selection-rect="selectionRect"
          :image-ref="imageRef"
          :current-device-id="currentDeviceId"
          @remove-color="removeColor"
          @clear-all-colors="clearAllColors"
          @add-colors="addColors"
          @remove-record-color="removeRecordColor"
          @clear-all-record-colors="clearAllRecordColors"
          @tab-change="handleRightTabChange"
          @right-panel-screenshot-start="handleRightPanelScreenshotStart"
          @right-panel-screenshot-end="handleRightPanelScreenshotEnd"
          @start-code-generator-selection="handleStartCodeGeneratorSelection"
          @stop-code-generator-selection="handleStopCodeGeneratorSelection"
          ref="rightPanelRef"
        />
      </div>
    </div>

    <!-- 设备连接弹框 -->
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
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { Picture, ZoomIn, Collection, Delete, Tools } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
import ImageProcessorLeftPanel from "./panels/ImageProcessorLeftPanel.vue";
import ImageProcessorRightPanel from "./panels/ImageProcessorRightPanel.vue";
import ImageProcessorDeviceDialog from "./dialogs/ImageProcessorDeviceDialog.vue";

// 文件输入引用
const fileInputRef = ref(null);
const imageRef = ref(null);
const imageContainerRef = ref(null);
const imageWrapperRef = ref(null);
const rightPanelRef = ref(null);

// 图片数组
const images = ref([]);
const currentImageIndex = ref("0");

// 是否启用圈选功能
const selectionEnabled = ref(false);
// 是否启用颜色选择功能（仅在启动圈选且没有圈选范围时启用）
const colorSelectionEnabled = ref(false);
// 代码生成器圈选模式（独立于左侧圈选功能）
const codeGeneratorSelectionEnabled = ref(false);

// 当前图片的计算属性
const currentImage = computed(() => {
  const index =
    typeof currentImageIndex.value === "string"
      ? parseInt(currentImageIndex.value)
      : currentImageIndex.value;
  if (
    images.value.length === 0 ||
    isNaN(index) ||
    index < 0 ||
    index >= images.value.length
  ) {
    return null;
  }
  return images.value[index];
});

// 当前图片的URL（用于兼容现有代码）
const imageUrl = computed(() => currentImage.value?.url || null);

// 当前图片的信息（用于兼容现有代码）
const imageInfo = computed(() => currentImage.value?.info || null);

// 当前图片的选中颜色列表（用于偏色计算）
const currentSelectedColors = computed(() => {
  if (!currentImage.value) return [];
  return currentImage.value.selectedColors || [];
});

// 颜色记录列表（用于颜色记录 tab）
const recordedColors = ref([]);

// 右侧面板当前激活的 tab
const activeRightTab = ref("deviation");

// 放大镜相关
const magnifierVisible = ref(false);
const mousePosition = ref({ x: 0, y: 0 });
const currentColor = ref(null);
const currentPosition = ref({ x: 0, y: 0 }); // 当前鼠标位置的图片坐标

// 圈选相关
const isSelecting = ref(false);
const isResizing = ref(false); // 是否在拖拉边框
const selectionStart = ref(null); // { imageX, imageY, naturalX, naturalY }
const selectionCurrent = ref(null); // { imageX, imageY, naturalX, naturalY }
const selectionDisplay = ref(null); // 用于在页面上显示的矩形（基于图片显示尺寸坐标）
const selectionRect = ref(null); // 基于原始图片坐标的矩形 { x, y, w, h }
const resizeHandle = ref(null); // 当前拖动的边/角方向，例如 left/right/top/bottom/top-left 等
const containerCursor = ref("default"); // 容器鼠标样式
const previousSelectionDisplay = ref(null); // 保存的旧选区显示矩形（用于点击时恢复）
const previousSelectionRect = ref(null); // 保存的旧选区原始坐标矩形（用于点击时恢复）

// 代码生成器圈选相关（独立状态）
const codeGeneratorSelectionStart = ref(null);
const codeGeneratorSelectionCurrent = ref(null);
const codeGeneratorSelectionRect = ref(null);
const codeGeneratorSelectionDisplay = ref(null); // 用于在页面上显示的矩形（基于图片显示尺寸坐标）
const codeGeneratorSelectionType = ref(null); // 'searchArea' | 'clickOffsetArea'

// 对外显示的圈选信息
const selectionInfo = computed(() => selectionRect.value);

// 图片尺寸
const imageNaturalSize = ref({ width: 0, height: 0 });

// 图片缩放和位置状态
const imageScale = ref(1); // 缩放比例
const imageTranslateX = ref(0); // X轴偏移
const imageTranslateY = ref(0); // Y轴偏移
const initialScale = ref(1); // 初始缩放比例（用于重置）
const initialTranslateX = ref(0); // 初始X偏移
const initialTranslateY = ref(0); // 初始Y偏移

// 拖动相关
const isDragging = ref(false);
const suppressNextClick = ref(false); // 拖动或圈选结束后抑制下一次click事件，防止误触发颜色选取
const dragStartX = ref(0);
const dragStartY = ref(0);
const dragStartTranslateX = ref(0);
const dragStartTranslateY = ref(0);
const isSpacePressed = ref(false); // 空格键按下状态（用于拖动图片）
let _skipSaveOnSwitch = false; // 删除图片时跳过 watch 中的保存逻辑

// 设备连接相关
const deviceDialogVisible = ref(false);
const deviceTab = ref("mobile");
const deviceList = ref([]);
const deviceLoading = ref(false);
const selectedDeviceId = ref("");
const currentDeviceId = ref("");
const screenshotLoading = ref(false);
const captureWindowLoading = ref(false);
const isRightPanelScreenshoting = ref(false); // 标记右侧面板是否正在截图
let deviceSocket = null;


// 载入图片
function handleLoadImage() {
  fileInputRef.value?.click();
}

// 打开设备连接弹框
function openDeviceDialog() {
  deviceDialogVisible.value = true;
  if (!deviceSocket) {
    initDeviceSocket();
  }
  refreshDevices();
}

// 处理文件选择
function handleFileSelect(event) {
  const files = Array.from(event.target.files || []);
  if (files.length === 0) return;

  // 过滤出图片文件
  const imageFiles = files.filter((file) => file.type.startsWith("image/"));

  if (imageFiles.length === 0) {
    ElMessage.error("请选择图片文件");
    return;
  }

  // 处理每个图片文件
  imageFiles.forEach((file) => {
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
            format: file.type.split("/")[1].toUpperCase(),
            width: img.width,
            height: img.height,
          },
          selectedColors: [],
          selectionRect: null, // 每张图片独立的圈选区域（基于原始图片坐标）
        };

        images.value.push(imageData);

        // 如果是第一张图片，自动选中
        if (images.value.length === 1) {
          currentImageIndex.value = "0";
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
  event.target.value = "";
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

// 图片加载完成
function handleImageLoad() {
  if (imageRef.value) {
    imageNaturalSize.value = {
      width: imageRef.value.naturalWidth,
      height: imageRef.value.naturalHeight,
    };
    // 图片加载后，计算初始缩放和位置（居中显示）
    nextTick(() => {
      calculateInitialTransform();
      // 图片加载并计算完缩放后，根据 selectionRect（原始坐标）恢复 selectionDisplay（显示坐标）
      if (selectionRect.value) {
        selectionDisplay.value = {
          x: selectionRect.value.x * imageScale.value,
          y: selectionRect.value.y * imageScale.value,
          w: selectionRect.value.w * imageScale.value,
          h: selectionRect.value.h * imageScale.value,
        };
      }
    });
  }
}

// 计算初始变换（居中显示）
function calculateInitialTransform() {
  if (!imageRef.value || !imageContainerRef.value) return;

  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const imgWidth = imageRef.value.naturalWidth;
  const imgHeight = imageRef.value.naturalHeight;

  // 计算适合容器的缩放比例（保持宽高比，最大边占满）
  const scaleX = containerRect.width / imgWidth;
  const scaleY = containerRect.height / imgHeight;
  const scale = Math.min(scaleX, scaleY, 1); // 不超过原始大小

  imageScale.value = scale;
  initialScale.value = scale;

  // 居中显示
  const scaledWidth = imgWidth * scale;
  const scaledHeight = imgHeight * scale;
  imageTranslateX.value = (containerRect.width - scaledWidth) / 2;
  imageTranslateY.value = (containerRect.height - scaledHeight) / 2;
  initialTranslateX.value = imageTranslateX.value;
  initialTranslateY.value = imageTranslateY.value;
}

// 图片包装器样式（用于定位）
const imageWrapperStyle = computed(() => {
  return {
    transform: `translate(${imageTranslateX.value}px, ${imageTranslateY.value}px)`,
    position: "absolute",
    top: 0,
    left: 0,
    cursor: isDragging.value
      ? "grabbing"
      : isSpacePressed.value
      ? "grab"
      : selectionEnabled.value
      ? containerCursor.value
      : "default",
  };
});

// 图片样式（用于缩放）
const imageStyle = computed(() => {
  return {
    transform: `scale(${imageScale.value})`,
    transformOrigin: "top left",
    display: "block",
  };
});

// ==================== 设备连接逻辑 ====================

function initDeviceSocket() {
  deviceSocket = io("ws://localhost:7070");

  deviceSocket.on("connect", () => {
    console.log("设备 Socket 连接成功");
  });

  deviceSocket.on("device-list", (data) => {
    console.log("收到设备列表:", data);
    handleDeviceList(data);
  });

  deviceSocket.on("device-selected", (data) => {
    console.log("收到设备选择结果:", data);
    handleDeviceSelected(data);
  });

  deviceSocket.on("device-screenshot", (data) => {
    console.log("收到设备截图:", data);
    handleDeviceScreenshot(data);
  });
}

function handleDeviceList(data) {
  deviceLoading.value = false;

  if (!data || !data.success) {
    ElMessage.error(data?.error || "获取设备列表失败");
    deviceList.value = [];
    return;
  }

  deviceList.value = data.devices || [];

  if (data.currentDeviceId) {
    currentDeviceId.value = data.currentDeviceId;
    selectedDeviceId.value = data.currentDeviceId;
  } else if (deviceList.value.length > 0 && !selectedDeviceId.value) {
    selectedDeviceId.value = deviceList.value[0];
  }
}

function handleDeviceSelected(data) {
  if (!data || !data.success) {
    ElMessage.error(data?.error || "连接设备失败");
    return;
  }

  currentDeviceId.value = data.currentDeviceId || "";

  if (currentDeviceId.value) {
    selectedDeviceId.value = currentDeviceId.value;
    ElMessage.success(`已连接设备: ${currentDeviceId.value}`);
  } else {
    ElMessage.info("已清除当前连接设备");
  }
}

function handleDeviceScreenshot(data) {
  // 检查截图来源，如果是右侧面板发起的，则忽略（由右侧面板自己处理）
  const source = data?.source;
  if (source === "right-panel") {
    console.log("忽略右侧面板的截图，由右侧面板自己处理");
    return;
  }
  
  // 检查截图来源，如果是图片匹配调试组件发起的，则忽略（由图片匹配调试组件自己处理）
  if (source === "image-match-debug") {
    console.log("忽略图片匹配调试组件的截图，由图片匹配调试组件自己处理");
    return;
  }
  
  // 兼容旧逻辑：如果数据中没有 source，但标志已设置，也忽略
  if (isRightPanelScreenshoting.value && !source) {
    console.log("忽略右侧面板的截图（通过标志判断），由右侧面板自己处理");
    return;
  }

  screenshotLoading.value = false;

  if (!data || !data.success || !data.image) {
    ElMessage.error(data?.error || "获取截图失败");
    return;
  }

  const url = `data:image/png;base64,${data.image}`;
  const img = new Image();
  img.onload = () => {
    const imageData = {
      name: `手机截图_${new Date().toLocaleTimeString()}.png`,
      url,
      file: null,
      info: {
        fileSize: "--",
        format: "PNG",
        width: img.width,
        height: img.height,
      },
      selectedColors: [],
      selectionRect: null, // 每张图片独立的圈选区域（基于原始图片坐标）
    };

    images.value.push(imageData);
    currentImageIndex.value = String(images.value.length - 1);
  };
  img.src = url;
}

async function refreshDevices() {
  deviceLoading.value = true;
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "get_devices",
    });
  } catch (error) {
    console.error("刷新设备失败:", error);
    ElMessage.error(`刷新设备失败: ${error.message || "未知错误"}`);
    deviceLoading.value = false;
  }
}

async function connectSelectedDevice() {
  if (!selectedDeviceId.value) return;
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "set_device",
      deviceId: selectedDeviceId.value,
    });
  } catch (error) {
    console.error("连接设备失败:", error);
    ElMessage.error(`连接设备失败: ${error.message || "未知错误"}`);
  }
}

// 处理右侧面板开始截图
function handleRightPanelScreenshotStart() {
  isRightPanelScreenshoting.value = true;
}

// 处理右侧面板结束截图
function handleRightPanelScreenshotEnd() {
  isRightPanelScreenshoting.value = false;
}

// 启动代码生成器圈选模式
function handleStartCodeGeneratorSelection(type) {
  codeGeneratorSelectionEnabled.value = true;
  // type: 'searchArea' | 'clickOffsetArea' | 'clickArea' | 'fontClickOffsetArea' | 'configFontClickOffsetArea'
  codeGeneratorSelectionType.value = type;
  codeGeneratorSelectionStart.value = null;
  codeGeneratorSelectionCurrent.value = null;
  codeGeneratorSelectionRect.value = null;
  codeGeneratorSelectionDisplay.value = null;
}

// 停止代码生成器圈选模式
function handleStopCodeGeneratorSelection() {
  codeGeneratorSelectionEnabled.value = false;
  codeGeneratorSelectionType.value = null;
  codeGeneratorSelectionStart.value = null;
  codeGeneratorSelectionCurrent.value = null;
  codeGeneratorSelectionRect.value = null;
  codeGeneratorSelectionDisplay.value = null;
}

async function captureScreenshot() {
  if (!currentDeviceId.value) {
    ElMessage.warning("请先连接设备");
    return;
  }

  screenshotLoading.value = true;
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "capture_screenshot",
      source: "left-panel", // 添加来源标识
    });
  } catch (error) {
    console.error("截图失败:", error);
    ElMessage.error(`截图失败: ${error.message || "未知错误"}`);
    screenshotLoading.value = false;
  }
}

async function openCaptureWindow() {
  try {
    const result = await ipc.invoke(ipcApiRoute.openCaptureWindow, {});
    if (result?.success) {
      ElMessage.success("截屏窗口已打开，可拖动调整区域后点击「截图」");
    } else {
      ElMessage.warning(result?.message || "打开截屏窗口失败");
    }
  } catch (err) {
    console.error("打开截屏窗口失败:", err);
    ElMessage.error(`打开截屏窗口失败: ${err?.message || "未知错误"}`);
  }
}

async function captureWindowScreenshot() {
  try {
    const status = await ipc.invoke(ipcApiRoute.getCaptureStatus, {});
    if (!status?.hasCaptureWindow) {
      ElMessage.warning("请先打开截屏窗口");
      return;
    }
    captureWindowLoading.value = true;
    const result = await ipc.invoke(ipcApiRoute.captureScreenOnce, {});
    if (!result?.success || !result?.image) {
      captureWindowLoading.value = false;
      ElMessage.error(result?.message || "截图失败");
      return;
    }
    captureWindowLoading.value = false;
    const url = result.image.startsWith("data:") ? result.image : `data:image/png;base64,${result.image}`;
    const img = new Image();
    img.onload = () => {
      const imageData = {
        name: `截屏窗口_${new Date().toLocaleTimeString()}.png`,
        url,
        file: null,
        info: {
          fileSize: "--",
          format: "PNG",
          width: img.width,
          height: img.height,
        },
        selectedColors: [],
        selectionRect: null,
      };
      images.value.push(imageData);
      currentImageIndex.value = String(images.value.length - 1);
      ElMessage.success("已截取截屏窗口区域");
    };
    img.src = url;
  } catch (err) {
    console.error("截屏窗口截图失败:", err);
    captureWindowLoading.value = false;
    ElMessage.error(`截图失败: ${err?.message || "未知错误"}`);
  }
}

function handleCaptureScreenshot() {
  if (deviceTab.value === "capture-window") {
    captureWindowScreenshot();
  } else {
    captureScreenshot();
  }
}

// 容器鼠标移动处理（在整个容器区域内都显示放大镜）
function handleContainerMouseMove(event) {
  if (!currentImage.value || !imageRef.value) {
    magnifierVisible.value = false;
    return;
  }

  // 如果正在拖动图片
  if (isDragging.value) {
    const deltaX = event.clientX - dragStartX.value;
    const deltaY = event.clientY - dragStartY.value;
    imageTranslateX.value = dragStartTranslateX.value + deltaX;
    imageTranslateY.value = dragStartTranslateY.value + deltaY;
    // 拖动时设置鼠标样式为小手
    containerCursor.value = "grabbing";
    return;
  }

  // 确保图片已加载完成
  if (
    !imageRef.value.complete ||
    imageRef.value.naturalWidth === 0 ||
    imageRef.value.naturalHeight === 0
  ) {
    magnifierVisible.value = false;
    return;
  }

  // 放大镜模式
  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const containerX = event.clientX - containerRect.left;
  const containerY = event.clientY - containerRect.top;

  // 检查鼠标是否在容器内
  if (
    containerX < 0 ||
    containerX >= containerRect.width ||
    containerY < 0 ||
    containerY >= containerRect.height
  ) {
    magnifierVisible.value = false;
    currentColor.value = null;
    return;
  }

  mousePosition.value = { x: containerX, y: containerY };

  // 计算图片在容器中的实际显示位置（考虑缩放和偏移）
  const imgNaturalWidth = imageRef.value.naturalWidth;
  const imgNaturalHeight = imageRef.value.naturalHeight;
  const imgDisplayWidth = imgNaturalWidth * imageScale.value;
  const imgDisplayHeight = imgNaturalHeight * imageScale.value;

  // 计算鼠标相对于图片显示区域的坐标（考虑图片的偏移）
  const imageX = containerX - imageTranslateX.value;
  const imageY = containerY - imageTranslateY.value;

  // 转换为图片原始尺寸的坐标
  const naturalX = imageX / imageScale.value;
  const naturalY = imageY / imageScale.value;

  // 限制到图片范围内（边缘像素）
  const clampedNaturalX = Math.max(0, Math.min(naturalX, imgNaturalWidth - 1));
  const clampedNaturalY = Math.max(0, Math.min(naturalY, imgNaturalHeight - 1));

  // 检查是否在图片显示区域内（用于圈选和鼠标样式）
  const isOnImage =
    imageX >= 0 && imageX < imgDisplayWidth && imageY >= 0 && imageY < imgDisplayHeight;

  // 如果鼠标在图片上，处理圈选相关逻辑
  if (isOnImage) {
    // 代码生成器圈选模式（优先级最高，独立处理）
    if (codeGeneratorSelectionEnabled.value) {
      containerCursor.value = "crosshair";
      // 更新代码生成器圈选时的矩形
      if (codeGeneratorSelectionStart.value) {
        codeGeneratorSelectionCurrent.value = {
          imageX,
          imageY,
          naturalX: clampedNaturalX,
          naturalY: clampedNaturalY,
        };
        updateCodeGeneratorSelectionRects();
      }
    } else if (selectionEnabled.value) {
      // 更新鼠标样式（仅在启用圈选时显示十字或缩放光标）
      updateCursorStyle(imageX, imageY);

      // 正在拖动边框调整大小
      if (isResizing.value && selectionDisplay.value && resizeHandle.value) {
        updateSelectionRectsByResize(imageX, imageY);
      }

      // 更新圈选时的矩形
      if (isSelecting.value && selectionStart.value) {
        selectionCurrent.value = {
          imageX,
          imageY,
          naturalX: clampedNaturalX,
          naturalY: clampedNaturalY,
        };
        updateSelectionRects();
      }
    } else {
      containerCursor.value = "default";
    }
  } else {
    // 鼠标不在图片上，重置为默认样式
    if (!codeGeneratorSelectionEnabled.value) {
      containerCursor.value = "default";
    }
  }

  // 更新当前坐标和放大镜（无论鼠标是否在图片上，都显示放大镜）
  currentPosition.value = {
    x: Math.floor(clampedNaturalX),
    y: Math.floor(clampedNaturalY),
  };
  magnifierVisible.value = true;
  // 使用 nextTick 确保 canvas 已渲染
  nextTick(() => {
    updateMagnifier(clampedNaturalX, clampedNaturalY);
  });
  updateCurrentColor(clampedNaturalX, clampedNaturalY);
}

// 鼠标进入容器
function handleMouseEnter() {
  // 鼠标进入时不做特殊处理，保持当前状态
}

// 鼠标离开容器
function handleMouseLeave() {
  // 只关闭放大镜与当前颜色显示，不修改已有圈选框
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
  
  if (codeGeneratorSelectionEnabled.value) {
    containerCursor.value = "crosshair";
  } else {
    containerCursor.value = selectionEnabled.value ? "crosshair" : "default";
  }

  // 不清除 selectionDisplay / selectionRect，保证圈选框在滚动时仍然存在
  // 也不强制修改 isSelecting / isResizing，避免与正在进行的其它操作冲突
}

// 鼠标按下开始圈选或拖动
function handleMouseDown(event) {
  if (!currentImage.value || !imageRef.value) return;

  // 仅响应左键
  if (event.button !== 0) return;

  // 按住空格键时，无论处于何种模式，都优先进入拖动图片模式
  if (isSpacePressed.value) {
    isDragging.value = true;
    dragStartX.value = event.clientX;
    dragStartY.value = event.clientY;
    dragStartTranslateX.value = imageTranslateX.value;
    dragStartTranslateY.value = imageTranslateY.value;
    event.preventDefault();
    return;
  }

  // 代码生成器圈选模式（优先级最高，独立处理）
  if (codeGeneratorSelectionEnabled.value) {
    const containerRect = imageContainerRef.value.getBoundingClientRect();
    const containerX = event.clientX - containerRect.left;
    const containerY = event.clientY - containerRect.top;

    // 计算鼠标相对于图片显示区域的坐标（考虑图片的偏移）
    const imageX = containerX - imageTranslateX.value;
    const imageY = containerY - imageTranslateY.value;

    const imgDisplayWidth = imageRef.value.naturalWidth * imageScale.value;
    const imgDisplayHeight = imageRef.value.naturalHeight * imageScale.value;

    if (
      imageX < 0 ||
      imageY < 0 ||
      imageX >= imgDisplayWidth ||
      imageY >= imgDisplayHeight
    ) {
      return;
    }

    // 转换为图片原始尺寸的坐标
    const naturalX = imageX / imageScale.value;
    const naturalY = imageY / imageScale.value;

    codeGeneratorSelectionStart.value = {
      imageX,
      imageY,
      naturalX,
      naturalY,
    };
    codeGeneratorSelectionCurrent.value = { ...codeGeneratorSelectionStart.value };
    return;
  }

  // 如果未启用圈选功能，则允许拖动图片
  if (!selectionEnabled.value) {
    // 检查是否按住了Ctrl键，如果是则允许拖动
    if (event.ctrlKey || event.metaKey) {
      isDragging.value = true;
      dragStartX.value = event.clientX;
      dragStartY.value = event.clientY;
      dragStartTranslateX.value = imageTranslateX.value;
      dragStartTranslateY.value = imageTranslateY.value;
      event.preventDefault();
      return;
    }
    // 如果没有按住Ctrl，也允许拖动（方便操作）
    isDragging.value = true;
    dragStartX.value = event.clientX;
    dragStartY.value = event.clientY;
    dragStartTranslateX.value = imageTranslateX.value;
    dragStartTranslateY.value = imageTranslateY.value;
    return;
  }

  // 启用圈选功能时，优先处理圈选
  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const containerX = event.clientX - containerRect.left;
  const containerY = event.clientY - containerRect.top;

  // 计算鼠标相对于图片显示区域的坐标（考虑图片的偏移）
  const imageX = containerX - imageTranslateX.value;
  const imageY = containerY - imageTranslateY.value;

  const imgDisplayWidth = imageRef.value.naturalWidth * imageScale.value;
  const imgDisplayHeight = imageRef.value.naturalHeight * imageScale.value;

  if (
    imageX < 0 ||
    imageY < 0 ||
    imageX >= imgDisplayWidth ||
    imageY >= imgDisplayHeight
  ) {
    return;
  }

  // 如果已有选区，优先判断是否点击在边框附近，进入拖拉边框模式；
  // 如果没有点在边框上，保存旧选区并准备开始新的圈选（但不清除，等拖动确认后再清除）
  if (selectionDisplay.value || selectionRect.value) {
    const handle = selectionDisplay.value
      ? getResizeHandleAtPoint(imageX, imageY, selectionDisplay.value)
      : null;
    if (handle) {
      isResizing.value = true;
      resizeHandle.value = handle;
      isSelecting.value = false;
      return;
    }
    // 有圈选但没点到边框上：保存旧选区，准备开始新的圈选
    // 如果只是点击（未拖动），会在 handleMouseUp 中保持旧选区不变，允许选取颜色
    // 如果真正拖动，会在 handleMouseUp 中清除旧选区并创建新的
    previousSelectionDisplay.value = selectionDisplay.value ? { ...selectionDisplay.value } : null;
    previousSelectionRect.value = selectionRect.value ? { ...selectionRect.value } : null;
    // 不清除旧选区，等拖动确认后再决定
  } else {
    // 没有旧选区时，清空保存的旧选区信息
    previousSelectionDisplay.value = null;
    previousSelectionRect.value = null;
  }

  // 转换为图片原始尺寸的坐标
  const naturalX = imageX / imageScale.value;
  const naturalY = imageY / imageScale.value;

  isSelecting.value = true;
  isResizing.value = false;
  resizeHandle.value = null;
  selectionStart.value = {
    imageX,
    imageY,
    naturalX,
    naturalY,
  };
  selectionCurrent.value = { ...selectionStart.value };
}

// 鼠标抬起结束圈选或拖动
function handleMouseUp(event) {
  if (!imageRef.value || !imageContainerRef.value) return;

  // 代码生成器圈选模式（优先级最高，独立处理）
  if (codeGeneratorSelectionEnabled.value && codeGeneratorSelectionStart.value) {
    const containerRect = imageContainerRef.value.getBoundingClientRect();
    const containerX = event.clientX - containerRect.left;
    const containerY = event.clientY - containerRect.top;

    // 计算鼠标相对于图片显示区域的坐标（考虑图片的偏移）
    const imageX = containerX - imageTranslateX.value;
    const imageY = containerY - imageTranslateY.value;

    const imgDisplayWidth = imageRef.value.naturalWidth * imageScale.value;
    const imgDisplayHeight = imageRef.value.naturalHeight * imageScale.value;

    const clampedX = Math.min(Math.max(imageX, 0), imgDisplayWidth);
    const clampedY = Math.min(Math.max(imageY, 0), imgDisplayHeight);

    // 转换为图片原始尺寸的坐标
    const naturalX = clampedX / imageScale.value;
    const naturalY = clampedY / imageScale.value;

    // 检查是否是真正的拖动（而不是点击）
    const dragThreshold = 5; // 拖动阈值，像素
    const dx = Math.abs(clampedX - codeGeneratorSelectionStart.value.imageX);
    const dy = Math.abs(clampedY - codeGeneratorSelectionStart.value.imageY);
    const dragDistance = Math.sqrt(dx * dx + dy * dy);

    if (dragDistance >= dragThreshold) {
      // 真正的拖动，更新当前点并创建/更新圈选框
      codeGeneratorSelectionCurrent.value = {
        imageX: clampedX,
        imageY: clampedY,
        naturalX,
        naturalY,
      };
      updateCodeGeneratorSelectionRects();

      // 将结果传递给对应的右侧 Tab
      if (codeGeneratorSelectionRect.value && rightPanelRef.value) {
        const rect = codeGeneratorSelectionRect.value;
        // 来自代码生成 Tab 的圈选
        if (
          codeGeneratorSelectionType.value === "searchArea" ||
          codeGeneratorSelectionType.value === "clickArea" ||
          codeGeneratorSelectionType.value === "clickOffsetArea"
        ) {
          const codeGeneratorTabRef = rightPanelRef.value.getCodeGeneratorTabRef?.();
          if (codeGeneratorTabRef && codeGeneratorTabRef.setSearchAreaFromSelection) {
            codeGeneratorTabRef.setSearchAreaFromSelection(rect);
          }
        }
        // 来自偏色计算 Tab 的偏移点击区域圈选（颜色 Tab）
        else if (codeGeneratorSelectionType.value === "fontClickOffsetArea") {
          const colorSelectionTabRef = rightPanelRef.value.getColorSelectionTabRef?.();
          if (
            colorSelectionTabRef &&
            typeof colorSelectionTabRef.setFontClickOffsetAreaFromSelection === "function"
          ) {
            colorSelectionTabRef.setFontClickOffsetAreaFromSelection(rect);
          }
        }
        // 来自配置 Tab 的偏移点击区域圈选
        else if (codeGeneratorSelectionType.value === "configFontClickOffsetArea") {
          const configTabRef = rightPanelRef.value.getConfigTabRef?.();
          if (
            configTabRef &&
            typeof configTabRef.setFontClickOffsetAreaFromSelection === "function"
          ) {
            configTabRef.setFontClickOffsetAreaFromSelection(rect);
          }
        }
      }
      // 代码生成器/偏移点击区域圈选拖动结束后抑制click事件，防止误触发颜色选取
      suppressNextClick.value = true;
    } else {
      // 只是点击，清除显示矩形
      codeGeneratorSelectionDisplay.value = null;
    }

    // 重置状态
    codeGeneratorSelectionStart.value = null;
    codeGeneratorSelectionCurrent.value = null;
    return;
  }

  // 结束拖动（空格键拖动或普通拖动都直接返回，不继续处理圈选逻辑）
  if (isDragging.value) {
    isDragging.value = false;
    suppressNextClick.value = true; // 拖动结束后抑制click事件，防止误触发颜色选取
    return;
  }

  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const containerX = event.clientX - containerRect.left;
  const containerY = event.clientY - containerRect.top;

  // 计算鼠标相对于图片显示区域的坐标（考虑图片的偏移）
  const imageX = containerX - imageTranslateX.value;
  const imageY = containerY - imageTranslateY.value;

  const imgDisplayWidth = imageRef.value.naturalWidth * imageScale.value;
  const imgDisplayHeight = imageRef.value.naturalHeight * imageScale.value;

  const clampedX = Math.min(Math.max(imageX, 0), imgDisplayWidth);
  const clampedY = Math.min(Math.max(imageY, 0), imgDisplayHeight);

  // 转换为图片原始尺寸的坐标
  const naturalX = clampedX / imageScale.value;
  const naturalY = clampedY / imageScale.value;

  if (isSelecting.value && selectionStart.value) {
    // 检查是否是真正的拖动（而不是点击）
    const dragThreshold = 5; // 拖动阈值，像素
    const dx = Math.abs(clampedX - selectionStart.value.imageX);
    const dy = Math.abs(clampedY - selectionStart.value.imageY);
    const dragDistance = Math.sqrt(dx * dx + dy * dy);

    if (dragDistance >= dragThreshold) {
      // 真正的拖动，清除旧圈选范围并创建新的圈选框
      if (previousSelectionDisplay.value || previousSelectionRect.value) {
        // 清除旧圈选范围
        selectionDisplay.value = null;
        selectionRect.value = null;
      }
      // 更新当前点并创建/更新圈选框
      selectionCurrent.value = {
        imageX: clampedX,
        imageY: clampedY,
        naturalX,
        naturalY,
      };
      updateSelectionRects();
      // 拖动创建新选区后，清空保存的旧选区信息
      previousSelectionDisplay.value = null;
      previousSelectionRect.value = null;
      // 圈选拖动结束后抑制click事件，防止误触发颜色选取
      suppressNextClick.value = true;
    } else {
      // 只是点击，不创建新圈选框，保持旧圈选范围不变（因为本来就没清除）
      // 重置本次拖拽状态
      selectionStart.value = null;
      selectionCurrent.value = null;
      // 清空保存的旧选区信息
      previousSelectionDisplay.value = null;
      previousSelectionRect.value = null;
    }
  }

  if (isResizing.value && selectionDisplay.value && selectionRect.value) {
    updateSelectionRectsByResize(clampedX, clampedY);
  }

  isSelecting.value = false;
  isResizing.value = false;
  resizeHandle.value = null;
}

// 右键点击：清除圈选框
function handleRightClick() {
  if (selectionDisplay.value || selectionRect.value) {
    clearSelection();
  }
}

  // 清空圈选相关状态
function clearSelection() {
  selectionDisplay.value = null;
  selectionRect.value = null;
  isSelecting.value = false;
  isResizing.value = false;
  selectionStart.value = null;
  selectionCurrent.value = null;
  resizeHandle.value = null;
  // 清空保存的旧选区信息
  previousSelectionDisplay.value = null;
  previousSelectionRect.value = null;
  // 同时清除当前图片上保存的圈选状态
  if (currentImage.value) {
    currentImage.value.selectionRect = null;
  }
  // 清空圈选后，如果圈选功能已启用，则启用颜色选择模式
  if (selectionEnabled.value) {
    colorSelectionEnabled.value = true;
  }
}

// 根据开始点和当前点，更新显示和原始坐标矩形
function updateSelectionRects() {
  if (!selectionStart.value || !selectionCurrent.value) return;

  const start = selectionStart.value;
  const curr = selectionCurrent.value;

  // 显示用矩形（基于图片显示尺寸）
  const x1 = start.imageX;
  const y1 = start.imageY;
  const x2 = curr.imageX;
  const y2 = curr.imageY;

  const dispX = Math.min(x1, x2);
  const dispY = Math.min(y1, y2);
  const dispW = Math.abs(x2 - x1);
  const dispH = Math.abs(y2 - y1);

  // 检查拖动距离是否足够大（防止点击时出现很小的圈选框）
  const dragThreshold = 5; // 拖动阈值，像素
  const dragDistance = Math.sqrt(dispW * dispW + dispH * dispH);

  if (dragDistance < dragThreshold) {
    // 拖动距离太小，不更新圈选框（保留原有圈选）
    return;
  }

  selectionDisplay.value = {
    x: dispX,
    y: dispY,
    w: dispW,
    h: dispH,
  };

  // 原始坐标矩形
  const nX1 = start.naturalX;
  const nY1 = start.naturalY;
  const nX2 = curr.naturalX;
  const nY2 = curr.naturalY;

  const natX = Math.floor(Math.max(0, Math.min(nX1, nX2)));
  const natY = Math.floor(Math.max(0, Math.min(nY1, nY2)));
  const natW = Math.floor(Math.abs(nX2 - nX1));
  const natH = Math.floor(Math.abs(nY2 - nY1));

  // 忽略过小的区域（防止误点）
  if (natW <= 0 || natH <= 0) {
    selectionRect.value = null;
    return;
  }

  selectionRect.value = {
    x: natX,
    y: natY,
    w: natW,
    h: natH,
  };

  // 同步保存圈选到当前图片
  if (currentImage.value) {
    currentImage.value.selectionRect = { ...selectionRect.value };
  }

  // 成功创建圈选范围后，禁用颜色选择模式
  colorSelectionEnabled.value = false;
}

// 更新代码生成器圈选矩形（不显示在页面上）
function updateCodeGeneratorSelectionRects() {
  if (!codeGeneratorSelectionStart.value || !codeGeneratorSelectionCurrent.value) return;

  const start = codeGeneratorSelectionStart.value;
  const curr = codeGeneratorSelectionCurrent.value;

  // 显示用矩形（基于图片显示尺寸）
  const x1 = start.imageX;
  const y1 = start.imageY;
  const x2 = curr.imageX;
  const y2 = curr.imageY;

  const dispX = Math.min(x1, x2);
  const dispY = Math.min(y1, y2);
  const dispW = Math.abs(x2 - x1);
  const dispH = Math.abs(y2 - y1);

  // 检查拖动距离是否足够大（防止点击时出现很小的圈选框）
  const dragThreshold = 5; // 拖动阈值，像素
  const dragDistance = Math.sqrt(dispW * dispW + dispH * dispH);

  if (dragDistance < dragThreshold) {
    // 拖动距离太小，不更新圈选框
    codeGeneratorSelectionDisplay.value = null;
    codeGeneratorSelectionRect.value = null;
    return;
  }

  codeGeneratorSelectionDisplay.value = {
    x: dispX,
    y: dispY,
    w: dispW,
    h: dispH,
  };

  // 原始坐标矩形
  const nX1 = start.naturalX;
  const nY1 = start.naturalY;
  const nX2 = curr.naturalX;
  const nY2 = curr.naturalY;

  const natX = Math.floor(Math.max(0, Math.min(nX1, nX2)));
  const natY = Math.floor(Math.max(0, Math.min(nY1, nY2)));
  const natW = Math.floor(Math.abs(nX2 - nX1));
  const natH = Math.floor(Math.abs(nY2 - nY1));

  // 忽略过小的区域（防止误点）
  if (natW <= 0 || natH <= 0) {
    codeGeneratorSelectionRect.value = null;
    return;
  }

  codeGeneratorSelectionRect.value = {
    x: natX,
    y: natY,
    w: natW,
    h: natH,
  };
}

// 圈选矩形样式（转换为 CSS 像素）
const selectionStyle = computed(() => {
  if (!selectionDisplay.value) return {};
  const rect = selectionDisplay.value;
  return {
    left: rect.x + "px",
    top: rect.y + "px",
    width: rect.w + "px",
    height: rect.h + "px",
  };
});

// 代码生成器圈选矩形样式（转换为 CSS 像素）
const codeGeneratorSelectionStyle = computed(() => {
  if (!codeGeneratorSelectionDisplay.value) return {};
  const rect = codeGeneratorSelectionDisplay.value;
  return {
    left: rect.x + "px",
    top: rect.y + "px",
    width: rect.w + "px",
    height: rect.h + "px",
  };
});

// 判断某个点是否在选区边框附近，返回拖动方向
function getResizeHandleAtPoint(x, y, rect) {
  const margin = 6; // 判定边框的容差
  const left = rect.x;
  const top = rect.y;
  const right = rect.x + rect.w;
  const bottom = rect.y + rect.h;

  const nearLeft = Math.abs(x - left) <= margin;
  const nearRight = Math.abs(x - right) <= margin;
  const nearTop = Math.abs(y - top) <= margin;
  const nearBottom = Math.abs(y - bottom) <= margin;

  // 先判断角
  if (nearLeft && nearTop) return "top-left";
  if (nearRight && nearTop) return "top-right";
  if (nearLeft && nearBottom) return "bottom-left";
  if (nearRight && nearBottom) return "bottom-right";

  // 再判断边
  const withinVertical = y >= top - margin && y <= bottom + margin;
  const withinHorizontal = x >= left - margin && x <= right + margin;
  if (nearLeft && withinVertical) return "left";
  if (nearRight && withinVertical) return "right";
  if (nearTop && withinHorizontal) return "top";
  if (nearBottom && withinHorizontal) return "bottom";

  return null;
}

// 更新鼠标样式
function updateCursorStyle(imageX, imageY) {
  // 如果正在拖动边框，保持相应的 cursor 样式
  if (isResizing.value && resizeHandle.value) {
    const cursorMap = {
      left: "ew-resize",
      right: "ew-resize",
      top: "ns-resize",
      bottom: "ns-resize",
      "top-left": "nw-resize",
      "top-right": "ne-resize",
      "bottom-left": "sw-resize",
      "bottom-right": "se-resize",
    };
    containerCursor.value = cursorMap[resizeHandle.value] || "crosshair";
    return;
  }

  // 如果正在圈选，使用 crosshair
  if (isSelecting.value) {
    containerCursor.value = "crosshair";
    return;
  }

  // 如果有选区，检测鼠标是否在边框附近
  if (selectionDisplay.value && selectionEnabled.value) {
    const handle = getResizeHandleAtPoint(imageX, imageY, selectionDisplay.value);
    if (handle) {
      const cursorMap = {
        left: "ew-resize",
        right: "ew-resize",
        top: "ns-resize",
        bottom: "ns-resize",
        "top-left": "nw-resize",
        "top-right": "ne-resize",
        "bottom-left": "sw-resize",
        "bottom-right": "se-resize",
      };
      containerCursor.value = cursorMap[handle] || "crosshair";
      return;
    }
  }

  // 默认样式（启用圈选时为十字，否则为默认）
  containerCursor.value = selectionEnabled.value ? "crosshair" : "default";
}

// 根据拖动边框更新矩形（传入的是当前鼠标在图片显示坐标中的位置）
function updateSelectionRectsByResize(imageX, imageY) {
  if (
    !selectionDisplay.value ||
    !selectionRect.value ||
    !imageRef.value ||
    !resizeHandle.value
  )
    return;

  const disp = { ...selectionDisplay.value };
  const minSize = 3; // 最小宽高，避免为 0

  let left = disp.x;
  let top = disp.y;
  let right = disp.x + disp.w;
  let bottom = disp.y + disp.h;

  const handle = resizeHandle.value;

  const imgDisplayWidth = imageRef.value.naturalWidth * imageScale.value;
  const imgDisplayHeight = imageRef.value.naturalHeight * imageScale.value;

  // 限制拖动点在图片显示范围内
  const clampX = Math.min(Math.max(imageX, 0), imgDisplayWidth);
  const clampY = Math.min(Math.max(imageY, 0), imgDisplayHeight);

  if (handle.includes("left")) {
    left = Math.min(clampX, right - minSize);
  } else if (handle.includes("right")) {
    right = Math.max(clampX, left + minSize);
  }

  if (handle.includes("top")) {
    top = Math.min(clampY, bottom - minSize);
  } else if (handle.includes("bottom")) {
    bottom = Math.max(clampY, top + minSize);
  }

  // 单独水平或垂直边（防止只含单词时遗漏）
  if (handle === "left") {
    left = Math.min(clampX, right - minSize);
  }
  if (handle === "right") {
    right = Math.max(clampX, left + minSize);
  }
  if (handle === "top") {
    top = Math.min(clampY, bottom - minSize);
  }
  if (handle === "bottom") {
    bottom = Math.max(clampY, top + minSize);
  }

  const newW = right - left;
  const newH = bottom - top;

  selectionDisplay.value = {
    x: left,
    y: top,
    w: newW,
    h: newH,
  };

  // 转换为原始图片坐标
  const natX = Math.floor(Math.max(0, left / imageScale.value));
  const natY = Math.floor(Math.max(0, top / imageScale.value));
  const natW = Math.floor(newW / imageScale.value);
  const natH = Math.floor(newH / imageScale.value);

  if (natW <= 0 || natH <= 0) {
    selectionRect.value = null;
    if (currentImage.value) {
      currentImage.value.selectionRect = null;
    }
    return;
  }

  selectionRect.value = {
    x: natX,
    y: natY,
    w: natW,
    h: natH,
  };

  // 同步保存圈选到当前图片（resize 操作）
  if (currentImage.value) {
    currentImage.value.selectionRect = { ...selectionRect.value };
  }
}

// 更新放大镜（x, y 是图片原始尺寸的坐标）
function updateMagnifier(x, y) {
  if (!rightPanelRef.value || !imageRef.value) return;

  // 确保图片已加载
  if (imageRef.value.naturalWidth === 0 || imageRef.value.naturalHeight === 0) return;

  const canvas = rightPanelRef.value.getMagnifierCanvas?.();
  if (!canvas) {
    // 如果 canvas 还未渲染，延迟重试
    setTimeout(() => {
      const retryCanvas = rightPanelRef.value?.getMagnifierCanvas?.();
      if (retryCanvas) {
        drawMagnifier(retryCanvas, x, y);
      }
    }, 10);
    return;
  }

  drawMagnifier(canvas, x, y);
}

// 绘制放大镜内容
function drawMagnifier(canvas, x, y) {
  if (!canvas || !imageRef.value) return;

  const ctx = canvas.getContext("2d");
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
  ctx.fillStyle = "#000000";
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
    sourceX,
    sourceY,
    sourceW,
    sourceH,
    drawX,
    drawY,
    sourceW * scale,
    sourceH * scale
  );

  // 绘制网格（每个像素一个格子）
  ctx.strokeStyle = "rgba(255, 255, 255, 0.8)";
  ctx.lineWidth = 1;
  ctx.lineCap = "square";

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

  // 中心像素高亮框 —— 仅在中心像素周围绘制醒目边框
  const centerBoxX = canvasCenterX - scale / 2;
  const centerBoxY = canvasCenterY - scale / 2;

  // 外层辉光（半透明白色）
  ctx.strokeStyle = "rgba(255, 255, 255, 0.5)";
  ctx.lineWidth = 3;
  ctx.strokeRect(centerBoxX - 1, centerBoxY - 1, scale + 2, scale + 2);

  // 内层精确框（亮红色）
  ctx.strokeStyle = "#ff3b3b";
  ctx.lineWidth = 1.5;
  ctx.strokeRect(centerBoxX, centerBoxY, scale, scale);
}

// 更新当前颜色（x, y 是图片原始尺寸的坐标）
function updateCurrentColor(x, y) {
  if (!imageRef.value) return;

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  canvas.width = imageRef.value.naturalWidth;
  canvas.height = imageRef.value.naturalHeight;
  ctx.drawImage(imageRef.value, 0, 0);

  const imageX = Math.floor(x);
  const imageY = Math.floor(y);

  if (imageX >= 0 && imageX < canvas.width && imageY >= 0 && imageY < canvas.height) {
    const imageData = ctx.getImageData(imageX, imageY, 1, 1);
    const [r, g, b] = imageData.data;
    const hex = `#${[r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("")}`;

    currentColor.value = {
      rgb: `rgb(${r}, ${g}, ${b})`,
      hex: hex.toUpperCase(),
    };
  }
}

// 图片点击处理
function handleImageClick(event) {
  if (!currentImage.value || !imageRef.value) return;

  // 如果刚刚完成了拖动或圈选操作，抑制本次click事件，防止误触发颜色选取
  if (suppressNextClick.value) {
    suppressNextClick.value = false;
    return;
  }

  // 如果正在圈选或调整大小，不处理点击事件
  if (isSelecting.value || isResizing.value) {
    return;
  }

  // 如果启用了颜色选择功能，执行颜色选择
  if (colorSelectionEnabled.value) {
    const containerRect = imageContainerRef.value.getBoundingClientRect();
    const containerX = event.clientX - containerRect.left;
    const containerY = event.clientY - containerRect.top;

    // 计算鼠标相对于图片显示区域的坐标（考虑图片的偏移）
    const imageX = containerX - imageTranslateX.value;
    const imageY = containerY - imageTranslateY.value;

    const imgDisplayWidth = imageRef.value.naturalWidth * imageScale.value;
    const imgDisplayHeight = imageRef.value.naturalHeight * imageScale.value;

    if (
      imageX >= 0 &&
      imageX < imgDisplayWidth &&
      imageY >= 0 &&
      imageY < imgDisplayHeight
    ) {
      if (currentColor.value) {
        // 转换为图片原始尺寸的坐标
        const naturalX = Math.floor(imageX / imageScale.value);
        const naturalY = Math.floor(imageY / imageScale.value);

        // 根据当前激活的 tab 决定记录到哪里
        if (activeRightTab.value === "deviation") {
          // 如果当前在偏色计算 tab，记录到 selectedColors（用于偏色计算）
          if (!currentImage.value.selectedColors) {
            currentImage.value.selectedColors = [];
          }

          // 检查是否已存在相同颜色的项
          const existingColorIndex = currentImage.value.selectedColors.findIndex(
            c => c.hex === currentColor.value.hex
          );
          
          if (existingColorIndex !== -1) {
            // 已存在相同颜色，仅提示，不重复添加
            ElMessage.warning("已经选取了相同颜色");
          } else {
            // 如果不存在，添加新项并设置个数为1，同时记录点击坐标
            currentImage.value.selectedColors.push({
              ...currentColor.value,
              count: 1,
              x: naturalX,
              y: naturalY,
            });
          }
        } else if (activeRightTab.value === "config") {
          // 如果当前在配置 tab，记录到 ConfigTab 的独立颜色列表
          const configTabRef = rightPanelRef.value?.getConfigTabRef?.();
          if (configTabRef?.addColor) {
            configTabRef.addColor(currentColor.value);
          }
        } else {
          // 默认记录到颜色记录 tab，记录坐标
          // 检查是否相同坐标点，避免重复记录
          const exists = recordedColors.value.some(
            c => c.x === naturalX && c.y === naturalY
          );
          if (!exists) {
            recordedColors.value.push({
              ...currentColor.value,
              x: naturalX,
              y: naturalY,
            });
          }
        }
      }
    }
    return;
  }

  // 如果有圈选范围，需要特殊处理
  if (selectionEnabled.value && selectionDisplay.value && selectionRect.value) {
    const containerRect = imageContainerRef.value.getBoundingClientRect();
    const containerX = event.clientX - containerRect.left;
    const containerY = event.clientY - containerRect.top;

    // 计算鼠标相对于图片显示区域的坐标（考虑图片的偏移）
    const imageX = containerX - imageTranslateX.value;
    const imageY = containerY - imageTranslateY.value;

    const imgDisplayWidth = imageRef.value.naturalWidth * imageScale.value;
    const imgDisplayHeight = imageRef.value.naturalHeight * imageScale.value;

    if (
      imageX >= 0 &&
      imageX < imgDisplayWidth &&
      imageY >= 0 &&
      imageY < imgDisplayHeight
    ) {
      const rect = selectionDisplay.value;
      const borderMargin = 6; // 边框容差，与getResizeHandleAtPoint中的margin保持一致

      // 检查是否点击在边框上（用于调整大小）
      const handle = getResizeHandleAtPoint(imageX, imageY, rect);
      if (handle) {
        // 点击在边框上，不处理（边框用于调整大小）
        return;
      }

      // 点击在圈选区域内部或外部，都允许选取颜色
      if (currentColor.value) {
        // 转换为图片原始尺寸的坐标
        const naturalX = Math.floor(imageX / imageScale.value);
        const naturalY = Math.floor(imageY / imageScale.value);

        // 根据当前激活的 tab 决定记录到哪里
        if (activeRightTab.value === "deviation") {
          // 如果当前在偏色计算 tab，记录到 selectedColors（用于偏色计算）
          if (!currentImage.value.selectedColors) {
            currentImage.value.selectedColors = [];
          }

          // 检查是否已存在相同颜色的项
          const existingColorIndex = currentImage.value.selectedColors.findIndex(
            c => c.hex === currentColor.value.hex
          );
          
          if (existingColorIndex !== -1) {
            // 已存在相同颜色，仅提示，不重复添加
            ElMessage.warning("已经选取了相同颜色");
          } else {
            // 如果不存在，添加新项并设置个数为1，同时记录点击坐标
            currentImage.value.selectedColors.push({
              ...currentColor.value,
              count: 1,
              x: naturalX,
              y: naturalY,
            });
          }
        } else if (activeRightTab.value === "config") {
          // 如果当前在配置 tab，记录到 ConfigTab 的独立颜色列表
          const configTabRef = rightPanelRef.value?.getConfigTabRef?.();
          if (configTabRef?.addColor) {
            configTabRef.addColor(currentColor.value);
          }
        } else {
          // 默认记录到颜色记录 tab，记录坐标
          // 检查是否相同坐标点，避免重复记录
          const exists = recordedColors.value.some(
            c => c.x === naturalX && c.y === naturalY
          );
          if (!exists) {
            recordedColors.value.push({
              ...currentColor.value,
              x: naturalX,
              y: naturalY,
            });
          }
        }
      }
    }
    return;
  }

  // 当在配置 tab 且「添加字库配置」抽屉打开时，允许直接点击图片选取颜色（无需开启圈选）
  if (activeRightTab.value === "config") {
    const configTabRef = rightPanelRef.value?.getConfigTabRef?.();
    if (typeof configTabRef?.isDrawerOpen === "function" && configTabRef.isDrawerOpen()) {
      const containerRect = imageContainerRef.value.getBoundingClientRect();
      const containerX = event.clientX - containerRect.left;
      const containerY = event.clientY - containerRect.top;
      const imageX = containerX - imageTranslateX.value;
      const imageY = containerY - imageTranslateY.value;
      const imgDisplayWidth = imageRef.value.naturalWidth * imageScale.value;
      const imgDisplayHeight = imageRef.value.naturalHeight * imageScale.value;
      if (
        imageX >= 0 &&
        imageX < imgDisplayWidth &&
        imageY >= 0 &&
        imageY < imgDisplayHeight
      ) {
        const naturalX = Math.floor(imageX / imageScale.value);
        const naturalY = Math.floor(imageY / imageScale.value);
        updateCurrentColor(naturalX, naturalY);
        if (currentColor.value && configTabRef.addColor) {
          configTabRef.addColor(currentColor.value);
        }
      }
      return;
    }
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

// 处理右侧 tab 切换
function handleRightTabChange(tabName) {
  activeRightTab.value = tabName;
}

// 移除颜色记录
function removeRecordColor(index) {
  recordedColors.value.splice(index, 1);
}

// 清空所有颜色记录
function clearAllRecordColors() {
  recordedColors.value = [];
}

// 添加统计的颜色
function addColors(colorStats) {
  if (!currentImage.value) {
    return;
  }

  // 确保当前图片有颜色数组
  if (!currentImage.value.selectedColors) {
    currentImage.value.selectedColors = [];
  }

  // 将统计的颜色添加到列表中，合并相同颜色的计数
  colorStats.forEach((colorStat) => {
    const existingColorIndex = currentImage.value.selectedColors.findIndex(
      (c) => c.hex === colorStat.hex
    );

    if (existingColorIndex !== -1) {
      // 如果已存在相同颜色，累加个数
      const existingColor = currentImage.value.selectedColors[existingColorIndex];
      existingColor.count = (existingColor.count || 1) + colorStat.count;
    } else {
      // 如果不存在，添加新项
      currentImage.value.selectedColors.push({
        hex: colorStat.hex,
        rgb: colorStat.rgb,
        count: colorStat.count,
      });
    }
  });
}

// 移除图片
function removeImage(index) {
  const removeIndex = typeof index === "string" ? parseInt(index) : index;

  if (images.value.length <= 1) {
    ElMessage.warning("至少需要保留一张图片");
    return;
  }

  const currentIndex =
    typeof currentImageIndex.value === "string"
      ? parseInt(currentImageIndex.value)
      : currentImageIndex.value;

  // 删除图片前，先保存当前图片的圈选到图片数据（如果删的不是当前图片）
  if (currentIndex !== removeIndex && currentImage.value) {
    currentImage.value.selectionRect = selectionRect.value
      ? { ...selectionRect.value }
      : null;
  }

  // 标记跳过 watch 中的保存逻辑（因为 splice 后旧索引已失效）
  _skipSaveOnSwitch = true;

  images.value.splice(removeIndex, 1);

  // 调整当前索引
  if (currentIndex >= images.value.length) {
    currentImageIndex.value = String(images.value.length - 1);
  } else if (currentIndex > removeIndex) {
    currentImageIndex.value = String(currentIndex - 1);
  } else if (currentIndex === removeIndex) {
    // 如果删除的是当前图片，切换到前一张或后一张
    currentImageIndex.value = String(Math.min(removeIndex, images.value.length - 1));
  } else {
    // 删除的是当前图片之后的，索引不变，watch 不触发，需要重置 _skipSaveOnSwitch
    _skipSaveOnSwitch = false;
  }

  // 重置放大镜和颜色
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
  containerCursor.value = selectionEnabled.value ? "crosshair" : "default";

  // 清除临时交互状态
  isSelecting.value = false;
  isResizing.value = false;
  resizeHandle.value = null;
  isDragging.value = false;
  selectionStart.value = null;
  selectionCurrent.value = null;
  previousSelectionDisplay.value = null;
  previousSelectionRect.value = null;

  // 从新的当前图片恢复圈选状态
  if (currentImage.value && currentImage.value.selectionRect) {
    selectionRect.value = { ...currentImage.value.selectionRect };
    // selectionDisplay 将在 handleImageLoad 中根据新的 imageScale 重新计算
    selectionDisplay.value = null;
  } else {
    selectionRect.value = null;
    selectionDisplay.value = null;
  }

  // 更新颜色选择模式
  if (selectionEnabled.value) {
    colorSelectionEnabled.value = !selectionRect.value;
  }
}

// 切换圈选功能开关
function toggleSelectionMode() {
  const wasEnabled = selectionEnabled.value;
  selectionEnabled.value = !selectionEnabled.value;

  // 关闭圈选功能时，清空已有圈选状态和颜色选择状态
  if (!selectionEnabled.value) {
    clearSelection();
    colorSelectionEnabled.value = false;
    return;
  }

  // 启动圈选功能时
  if (selectionEnabled.value && !wasEnabled) {
    // 如果没有圈选范围，启用颜色选择模式
    if (!selectionDisplay.value && !selectionRect.value) {
      colorSelectionEnabled.value = true;
    } else {
      // 如果有圈选范围，禁用颜色选择，进行圈选
      colorSelectionEnabled.value = false;
    }
  }
}

// 处理滚轮缩放（Ctrl + 滚轮）
function handleWheel(event) {
  if (!currentImage.value || !imageRef.value || !imageContainerRef.value) return;

  // 检查是否按住了Ctrl键
  if (!event.ctrlKey && !event.metaKey) {
    return; // 没有按住Ctrl，不处理缩放
  }

  event.preventDefault();

  // 获取容器和图片的位置信息
  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const mouseX = event.clientX - containerRect.left;
  const mouseY = event.clientY - containerRect.top;

  // 计算鼠标在图片上的相对位置（考虑当前缩放和偏移）
  const imgRect = imageRef.value.getBoundingClientRect();
  const imgX = (mouseX - imageTranslateX.value) / imageScale.value;
  const imgY = (mouseY - imageTranslateY.value) / imageScale.value;

  // 计算缩放增量
  const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(0.1, Math.min(10, imageScale.value * zoomFactor));

  // 计算新的偏移，使鼠标指向的图片位置保持不变
  const newTranslateX = mouseX - imgX * newScale;
  const newTranslateY = mouseY - imgY * newScale;

  imageScale.value = newScale;
  imageTranslateX.value = newTranslateX;
  imageTranslateY.value = newTranslateY;
}

// 自适应缩放（最大边占满，居中）
function fitToWindow() {
  if (!imageRef.value || !imageContainerRef.value || !currentImage.value) {
    ElMessage.warning("请先载入图片");
    return;
  }

  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const imgWidth = imageRef.value.naturalWidth;
  const imgHeight = imageRef.value.naturalHeight;

  if (imgWidth === 0 || imgHeight === 0) {
    ElMessage.warning("图片尺寸无效");
    return;
  }

  // 计算适合容器的缩放比例（保持宽高比，最大边占满）
  const scaleX = containerRect.width / imgWidth;
  const scaleY = containerRect.height / imgHeight;
  const scale = Math.min(scaleX, scaleY);

  imageScale.value = scale;

  // 居中显示
  const scaledWidth = imgWidth * scale;
  const scaledHeight = imgHeight * scale;
  imageTranslateX.value = (containerRect.width - scaledWidth) / 2;
  imageTranslateY.value = (containerRect.height - scaledHeight) / 2;

  ElMessage.success("已自适应缩放");
}

// 重置缩放
function resetZoom() {
  if (!currentImage.value) {
    ElMessage.warning("请先载入图片");
    return;
  }

  imageScale.value = initialScale.value;
  imageTranslateX.value = initialTranslateX.value;
  imageTranslateY.value = initialTranslateY.value;

  ElMessage.success("已重置缩放");
}

// 复制选区坐标到剪贴板 (x,y,w,h 格式)
function handleCopySelection() {
  if (!selectionRect.value) {
    ElMessage.warning("请先选择一个区域");
    return;
  }
  const { x, y, w, h } = selectionRect.value;
  const text = `${x},${y},${w},${h}`;
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success(`已复制: ${text}`);
  }).catch(() => {
    ElMessage.error("复制失败");
  });
}

// 裁剪图片
function handleCropImage() {
  if (!currentImage.value || !imageRef.value || !selectionRect.value) {
    ElMessage.warning("请先选择要裁剪的区域");
    return;
  }

  const rect = selectionRect.value;
  const img = imageRef.value;

  // 验证裁剪区域是否有效
  if (rect.w <= 0 || rect.h <= 0) {
    ElMessage.warning("裁剪区域无效");
    return;
  }

  // 确保裁剪区域在图片范围内
  const maxX = img.naturalWidth;
  const maxY = img.naturalHeight;
  const cropX = Math.max(0, Math.min(rect.x, maxX - 1));
  const cropY = Math.max(0, Math.min(rect.y, maxY - 1));
  const cropW = Math.min(rect.w, maxX - cropX);
  const cropH = Math.min(rect.h, maxY - cropY);

  if (cropW <= 0 || cropH <= 0) {
    ElMessage.warning("裁剪区域超出图片范围");
    return;
  }

  try {
    // 创建 canvas 进行裁剪
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    
    // 设置 canvas 尺寸为裁剪区域大小
    canvas.width = cropW;
    canvas.height = cropH;

    // 将裁剪区域绘制到 canvas
    ctx.drawImage(
      img,
      cropX, cropY, cropW, cropH,  // 源图片的裁剪区域
      0, 0, cropW, cropH            // 目标 canvas 的位置和尺寸
    );

    // 将 canvas 转换为 base64
    const base64Data = canvas.toDataURL("image/png");
    
    // 创建新的图片数据
    const timestamp = new Date().toLocaleTimeString();
    const originalName = currentImage.value.name || "image.png";
    const nameWithoutExt = originalName.replace(/\.[^/.]+$/, "");
    const extension = originalName.match(/\.[^/.]+$/) || ".png";
    const croppedName = `${nameWithoutExt}_cropped_${timestamp}${extension}`;

    const imageData = {
      name: croppedName,
      url: base64Data,
      file: null,
      info: {
        fileSize: "--",
        format: "PNG",
        width: cropW,
        height: cropH,
      },
      selectedColors: [],
      selectionRect: null, // 每张图片独立的圈选区域（基于原始图片坐标）
    };

    // 添加到图片数组
    images.value.push(imageData);
    
    // 自动切换到新创建的图片
    const newIndex = images.value.length - 1;
    currentImageIndex.value = String(newIndex);

    ElMessage.success("图片裁剪成功");
  } catch (error) {
    console.error("裁剪图片失败:", error);
    ElMessage.error(`裁剪图片失败: ${error.message || "未知错误"}`);
  }
}

// 保存图片
async function handleSaveImage() {
  if (!currentImage.value || !imageRef.value) {
    ElMessage.warning("请先载入图片");
    return;
  }

  try {
    // 打开保存对话框
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const defaultName = currentImage.value.name || `image_${timestamp}.png`;

    const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
      defaultName: defaultName,
    });

    if (!result || !result.success || result.canceled) {
      return; // 用户取消或对话框失败
    }

    // 如果图片 URL 是 base64 格式，直接提取 base64 数据
    let base64String = null;
    const imageUrl = currentImage.value.url;

    if (imageUrl.startsWith("data:")) {
      // 从 data URL 中提取 base64 字符串
      if (imageUrl.includes(",")) {
        base64String = imageUrl.split(",")[1];
      } else {
        base64String = imageUrl.replace(/^data:image\/\w+;base64,/, "");
      }
    } else {
      // 如果是 blob URL 或其他格式，需要将图片绘制到 canvas 再转换
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      
      // 设置 canvas 尺寸为图片原始尺寸
      canvas.width = imageRef.value.naturalWidth;
      canvas.height = imageRef.value.naturalHeight;

      // 绘制原始图片
      ctx.drawImage(imageRef.value, 0, 0);

      // 将 canvas 转换为 base64
      const base64Data = canvas.toDataURL("image/png");
      
      // 提取 base64 字符串（去掉 data:image/png;base64, 前缀）
      if (base64Data.includes(",")) {
        base64String = base64Data.split(",")[1];
      } else {
        base64String = base64Data.replace(/^data:image\/\w+;base64,/, "");
      }
    }

    if (!base64String) {
      throw new Error("无法提取图片数据");
    }

    // 通过 IPC 调用主进程保存文件
    const saveResult = await ipc.invoke(ipcApiRoute.saveBase64Image, {
      filePath: result.filePath,
      imageData: base64String,
    });

    if (saveResult && saveResult.success) {
      ElMessage.success("图片保存成功");
    } else {
      throw new Error(saveResult?.error || "保存失败");
    }
  } catch (error) {
    console.error("保存图片失败:", error);
    ElMessage.error(`保存图片失败: ${error.message || "未知错误"}`);
  }
}

// 监听当前图片切换，保存旧图片圈选、恢复新图片圈选
watch(currentImageIndex, (newVal, oldVal) => {
  // === 保存旧图片的圈选状态（删除图片时跳过，因为数组索引已变） ===
  if (!_skipSaveOnSwitch) {
    const oldIndex = typeof oldVal === "string" ? parseInt(oldVal) : oldVal;
    if (!isNaN(oldIndex) && oldIndex >= 0 && oldIndex < images.value.length) {
      images.value[oldIndex].selectionRect = selectionRect.value
        ? { ...selectionRect.value }
        : null;
    }
  }
  _skipSaveOnSwitch = false;

  // === 重置交互状态（放大镜、拖动等临时状态） ===
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
  isSelecting.value = false;
  isResizing.value = false;
  resizeHandle.value = null;
  containerCursor.value = selectionEnabled.value ? "crosshair" : "default";
  isDragging.value = false;
  selectionStart.value = null;
  selectionCurrent.value = null;
  previousSelectionDisplay.value = null;
  previousSelectionRect.value = null;

  // === 恢复新图片的圈选状态 ===
  const newIndex = typeof newVal === "string" ? parseInt(newVal) : newVal;
  if (!isNaN(newIndex) && newIndex >= 0 && newIndex < images.value.length) {
    const newImage = images.value[newIndex];
    selectionRect.value = newImage.selectionRect
      ? { ...newImage.selectionRect }
      : null;
  } else {
    selectionRect.value = null;
  }
  // selectionDisplay 将在 handleImageLoad 中根据新的 imageScale 重新计算
  selectionDisplay.value = null;

  // 更新颜色选择模式
  if (selectionEnabled.value) {
    colorSelectionEnabled.value = !selectionRect.value;
  }

  if (currentImage.value) {
    nextTick(() => {
      if (imageRef.value) {
        imageNaturalSize.value = {
          width: imageRef.value.naturalWidth,
          height: imageRef.value.naturalHeight,
        };
        // 切换图片时重新计算初始变换
        calculateInitialTransform();
        // 恢复圈选显示坐标（处理缓存图片不触发 @load 的情况）
        if (selectionRect.value && imageScale.value) {
          selectionDisplay.value = {
            x: selectionRect.value.x * imageScale.value,
            y: selectionRect.value.y * imageScale.value,
            w: selectionRect.value.w * imageScale.value,
            h: selectionRect.value.h * imageScale.value,
          };
        }
      }
    });
  }
});

// 监听缩放变化，同步更新选区显示坐标（使选区跟随图片缩放）
watch(imageScale, (newScale) => {
  // 更新圈选框显示坐标
  if (selectionRect.value) {
    selectionDisplay.value = {
      x: selectionRect.value.x * newScale,
      y: selectionRect.value.y * newScale,
      w: selectionRect.value.w * newScale,
      h: selectionRect.value.h * newScale,
    };
  }
  // 更新保存的旧选区显示坐标（用于点击恢复）
  if (previousSelectionRect.value) {
    previousSelectionDisplay.value = {
      x: previousSelectionRect.value.x * newScale,
      y: previousSelectionRect.value.y * newScale,
      w: previousSelectionRect.value.w * newScale,
      h: previousSelectionRect.value.h * newScale,
    };
  }
  // 更新代码生成器圈选框显示坐标
  if (codeGeneratorSelectionRect.value) {
    codeGeneratorSelectionDisplay.value = {
      x: codeGeneratorSelectionRect.value.x * newScale,
      y: codeGeneratorSelectionRect.value.y * newScale,
      w: codeGeneratorSelectionRect.value.w * newScale,
      h: codeGeneratorSelectionRect.value.h * newScale,
    };
  }
});

// 全局鼠标事件，确保在容器外也能正确结束圈选和拖动
function handleGlobalMouseUp(event) {
  if (isSelecting.value || isResizing.value) {
    // 如果正在圈选或调整大小，调用 handleMouseUp
    handleMouseUp(event);
  }
  // 结束拖动
  if (isDragging.value) {
    isDragging.value = false;
  }
}

// 处理键盘快捷键（Alt+D 切换选取模式，方向键移动放大镜像素选择，空格键拖动图片）
function handleKeyDown(event) {
  // 空格键按下：启用拖动模式（排除输入框等可编辑元素中的空格）
  if (event.code === 'Space') {
    const tag = event.target.tagName;
    const isEditable = event.target.isContentEditable;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || isEditable) {
      return; // 在输入框中不拦截空格
    }
    event.preventDefault(); // 防止页面滚动
    if (!isSpacePressed.value) {
      isSpacePressed.value = true;
    }
    return;
  }

  // 检查是否按下了 Alt+D
  if (event.altKey && event.key.toLowerCase() === 'd') {
    event.preventDefault(); // 防止浏览器默认行为
    toggleSelectionMode();
    return;
  }

  // 方向键移动放大镜像素选择
  const arrowKeys = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
  if (arrowKeys.includes(event.key) && currentImage.value && imageRef.value) {
    // 确保图片已加载完成
    if (!imageRef.value.complete || imageRef.value.naturalWidth === 0) return;

    event.preventDefault(); // 阻止页面滚动

    const imgWidth = imageRef.value.naturalWidth;
    const imgHeight = imageRef.value.naturalHeight;

    // 基于当前坐标移动
    let newX = currentPosition.value.x;
    let newY = currentPosition.value.y;

    switch (event.key) {
      case 'ArrowUp':
        newY = Math.max(0, newY - 1);
        break;
      case 'ArrowDown':
        newY = Math.min(imgHeight - 1, newY + 1);
        break;
      case 'ArrowLeft':
        newX = Math.max(0, newX - 1);
        break;
      case 'ArrowRight':
        newX = Math.min(imgWidth - 1, newX + 1);
        break;
    }

    // 更新当前坐标
    currentPosition.value = { x: newX, y: newY };

    // 显示放大镜
    magnifierVisible.value = true;

    // 更新放大镜和当前颜色
    nextTick(() => {
      updateMagnifier(newX, newY);
    });
    updateCurrentColor(newX, newY);
  }
}

// 处理键盘释放事件（主要用于空格键释放恢复状态）
function handleKeyUp(event) {
  if (event.code === 'Space') {
    isSpacePressed.value = false;
    // 如果正在拖动，结束拖动
    if (isDragging.value) {
      isDragging.value = false;
    }
  }
}

onMounted(() => {
  // 添加全局鼠标抬起事件监听
  document.addEventListener("mouseup", handleGlobalMouseUp);
  // 添加键盘事件监听（Alt+D 切换选取模式，空格键拖动等）
  document.addEventListener("keydown", handleKeyDown);
  document.addEventListener("keyup", handleKeyUp);
});

onUnmounted(() => {
  // 移除全局鼠标抬起事件监听
  document.removeEventListener("mouseup", handleGlobalMouseUp);
  // 移除键盘事件监听
  document.removeEventListener("keydown", handleKeyDown);
  document.removeEventListener("keyup", handleKeyUp);

  if (deviceSocket) {
    deviceSocket.disconnect();
    deviceSocket = null;
  }
});
</script>

<style scoped>
/* ===== 固定尺寸 ===== */
/* 1440 x 960 窗口, 标题栏40px, 内容区 920px */
/* 左220px | 中760px | 右460px = 1440px */

.image-processor-tab {
  width: 1440px;
  height: 920px;
  overflow: hidden;
  box-sizing: border-box;
}

.processor-layout {
  display: flex;
  width: 1440px;
  height: 920px;
  overflow: hidden;
}

/* ===== 左侧面板 ===== */
.left-panel {
  width: 220px;
  min-width: 220px;
  max-width: 220px;
  height: 920px;
  overflow: hidden;
  box-sizing: border-box;
}

/* ===== 中间面板 ===== */
.center-panel {
  width: 760px;
  min-width: 760px;
  max-width: 760px;
  height: 920px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  border-left: 1px solid rgba(99, 102, 241, 0.15);
  border-right: 1px solid rgba(99, 102, 241, 0.15);
  background: #0f172a;
}

/* ===== 右面板容器 ===== */
.right-panel {
  width: 460px;
  min-width: 460px;
  max-width: 460px;
  height: 920px;
  overflow: hidden;
  box-sizing: border-box;
}

/* 中间面板内的图片标签栏 */
.center-panel :deep(.el-tabs) {
  flex-shrink: 0;
  border: none;
}

.center-panel :deep(.el-tabs__header) {
  margin-bottom: 0;
  background: linear-gradient(180deg, #1e293b, #1a2332);
  border-bottom: 1px solid #334155;
}

.center-panel :deep(.el-tabs__item) {
  color: #94a3b8;
  border-color: #334155;
  font-size: 12px;
  font-weight: 500;
  height: 32px;
  line-height: 32px;
  transition: color 0.2s ease, background 0.2s ease;
}

.center-panel :deep(.el-tabs__item.is-active) {
  color: #e0e7ff;
  background: #0f172a;
  border-bottom-color: #0f172a;
  font-weight: 600;
}

.center-panel :deep(.el-tabs__item:hover) {
  color: #e2e8f0;
}

.center-panel :deep(.el-tabs--border-card) {
  border: none;
  background: transparent;
  box-shadow: none;
  padding: 0;
}

.center-panel :deep(.el-tabs__content) {
  display: none !important;
  padding: 0 !important;
  height: 0 !important;
  overflow: hidden;
}

/* 确保 border-card 底部不产生额外间隙 */
.center-panel :deep(.el-tabs--border-card > .el-tabs__header) {
  border-bottom: none;
}

/* 修复 Tab 左右滚动箭头位置偏下 */
.center-panel :deep(.el-tabs__nav-prev),
.center-panel :deep(.el-tabs__nav-next) {
  height: 32px;
  line-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Tab 关闭按钮 */
.center-panel :deep(.el-tabs__item .el-icon.is-icon-close) {
  color: #64748b;
  transition: all 0.15s ease;
}

.center-panel :deep(.el-tabs__item .el-icon.is-icon-close:hover) {
  color: #f87171;
  background: rgba(248, 113, 113, 0.15);
  border-radius: 50%;
}

/* ===== 图片容器 ===== */
.image-container {
  width: 100%;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: #0f172a;
  background-image:
    linear-gradient(45deg, #1e293b 25%, transparent 25%),
    linear-gradient(-45deg, #1e293b 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #1e293b 75%),
    linear-gradient(-45deg, transparent 75%, #1e293b 75%);
  background-size: 16px 16px;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
  position: relative;
  user-select: none;
  box-sizing: border-box;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(99, 102, 241, 0.2);
}

.image-wrapper {
  display: inline-block;
  position: relative;
  user-select: none;
}

/* 圈选矩形 */
.selection-rect {
  position: absolute;
  border: 2px solid #22c55e;
  background: rgba(34, 197, 94, 0.1);
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.4),
    inset 0 0 0 1px rgba(34, 197, 94, 0.2),
    0 0 12px rgba(34, 197, 94, 0.15);
  pointer-events: none;
  box-sizing: border-box;
  transition: box-shadow 0.2s ease;
}

/* 代码生成器圈选矩形 */
.code-generator-selection-rect {
  position: absolute;
  border: 2px solid #818cf8;
  background: rgba(129, 140, 248, 0.1);
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.4),
    inset 0 0 0 1px rgba(129, 140, 248, 0.2),
    0 0 12px rgba(129, 140, 248, 0.15);
  pointer-events: none;
  box-sizing: border-box;
  z-index: 10;
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

/* 空状态占位 */
.empty-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #475569;
  gap: 16px;
}

.empty-icon {
  font-size: 52px;
  color: #334155;
  opacity: 0.6;
  animation: empty-float 3s ease-in-out infinite;
}

@keyframes empty-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.empty-placeholder p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  letter-spacing: 0.5px;
  font-weight: 500;
}
</style>
