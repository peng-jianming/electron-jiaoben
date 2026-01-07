<template>
  <div class="image-processor-tab">
    <!-- 左中右布局 -->
    <div class="processor-layout">
      <!-- 左侧：功能按钮区域 -->
      <div class="left-panel">
        <div class="card">
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

            <div class="device-section">
              <div class="device-current">
                当前设备：<span>{{ currentDeviceId || '未连接' }}</span>
              </div>
              <el-button 
                type="success" 
                :icon="Tools"
                class="action-btn device-btn"
                @click="openDeviceDialog"
              >
                设备连接
              </el-button>
              <el-button 
                type="primary" 
                class="action-btn device-btn"
                :loading="screenshotLoading"
                :disabled="!currentDeviceId"
                @click="captureScreenshot"
              >
                截图
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：图片显示区域 -->
      <div class="center-panel">
        <div class="card">
          <div class="card-body image-container-wrapper">
            <!-- Tab 切换 -->
            <el-tabs 
              v-if="images.length >= 2"
                v-model="currentImageIndex" 
                type="card"
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
              :style="{ cursor: containerCursor }"
              @mousemove="handleContainerMouseMove"
              @mouseenter="handleMouseEnter"
              @mouseleave="handleMouseLeave"
              @mousedown="handleMouseDown"
              @mouseup="handleMouseUp"
              @contextmenu.prevent="handleRightClick"
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
                <!-- 圈选矩形高亮 -->
                <div 
                  v-if="selectionDisplay"
                  class="selection-rect"
                  :style="selectionStyle"
                ></div>
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
            <!-- 圈选区域信息 -->
            <div v-if="selectionInfo" class="selection-info">
              <span class="info-label">选区：</span>
              <span class="info-value">
                x={{ selectionInfo.x }}, y={{ selectionInfo.y }}, w={{ selectionInfo.w }}, h={{ selectionInfo.h }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：放大镜和颜色信息 -->
      <div class="right-panel">
        <!-- 放大镜 -->
        <div class="card">
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
            <div class="current-color">
              <div class="color-values">
                <div class="color-value-item">
                  <span class="color-label">坐标:</span>
                  <span class="color-value">({{ currentPosition ? currentPosition.x : '0' }}, {{ currentPosition ? currentPosition.y : '0' }})</span>
                </div>
                <div class="color-value-item">
                  <span class="color-label">RGB:</span>
                  <span class="color-value">{{ currentColor ? currentColor.rgb: '--' }}</span>
                </div>
                <div class="color-value-item">
                  <span class="color-label">HEX:</span>
                  <span class="color-value">{{ currentColor ? currentColor.hex: '--' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 选中颜色列表 -->
        <div class="card" style="flex: 1; overflow:auto">
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
                  <div class="color-coord-small">坐标: {{ color.x }}, {{ color.y }}</div>
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

    <!-- 设备连接弹框 -->
    <el-dialog
      v-model="deviceDialogVisible"
      title="设备连接"
      width="520px"
    >
      <el-tabs v-model="deviceTab">
        <el-tab-pane label="手机" name="mobile">
          <div class="device-toolbar">
            <el-button 
              size="small" 
              type="primary" 
              @click="refreshDevices" 
              :loading="deviceLoading"
            >
              刷新设备
            </el-button>
            <span class="device-tip">请确保手机已通过 USB 或 WiFi 连接到 ADB</span>
          </div>

          <div v-if="!deviceLoading && deviceList.length === 0" class="device-empty">
            <el-empty description="未发现设备，请点击刷新" />
          </div>

          <div v-else class="device-list-wrapper">
            <el-radio-group v-model="selectedDeviceId" class="device-list">
              <el-radio 
                v-for="id in deviceList" 
                :key="id" 
                :label="id"
              >
                {{ id }}
                <span 
                  v-if="currentDeviceId === id" 
                  class="device-tag"
                >
                  当前
                </span>
              </el-radio>
            </el-radio-group>
          </div>

          <div class="device-footer">
            <span class="device-footer-text">
              当前连接设备：{{ currentDeviceId || '未连接' }}
            </span>
            <el-button 
              type="primary" 
              size="small" 
              @click="connectSelectedDevice" 
              :disabled="!selectedDeviceId"
            >
              连接设备
            </el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="电脑" name="pc">
          <div class="device-placeholder">
            电脑连接功能开发中...
          </div>
        </el-tab-pane>

        <el-tab-pane label="虚拟机" name="vm">
          <div class="device-placeholder">
            虚拟机连接功能开发中...
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { Upload, Picture, ZoomIn, Collection, Delete, Tools } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { ipc } from '@/utils/ipcRenderer';
import { ipcApiRoute } from '@/api';
import { io } from 'socket.io-client';

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

// 圈选相关
const isSelecting = ref(false);
const isResizing = ref(false);      // 是否在拖拉边框
const selectionStart = ref(null);   // { imageX, imageY, naturalX, naturalY }
const selectionCurrent = ref(null); // { imageX, imageY, naturalX, naturalY }
const selectionDisplay = ref(null); // 用于在页面上显示的矩形（基于图片显示尺寸坐标）
const selectionRect = ref(null);    // 基于原始图片坐标的矩形 { x, y, w, h }
const resizeHandle = ref(null);     // 当前拖动的边/角方向，例如 left/right/top/bottom/top-left 等
const containerCursor = ref('crosshair'); // 容器鼠标样式

// 对外显示的圈选信息
const selectionInfo = computed(() => selectionRect.value);

// 图片尺寸
const imageNaturalSize = ref({ width: 0, height: 0 });

// 设备连接相关
const deviceDialogVisible = ref(false);
const deviceTab = ref('mobile');
const deviceList = ref([]);
const deviceLoading = ref(false);
const selectedDeviceId = ref('');
const currentDeviceId = ref('');
const screenshotLoading = ref(false);
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

// ==================== 设备连接逻辑 ====================

function initDeviceSocket() {
  deviceSocket = io('ws://localhost:7070');

  deviceSocket.on('connect', () => {
    console.log('设备 Socket 连接成功');
  });

  deviceSocket.on('device-list', (data) => {
    console.log('收到设备列表:', data);
    handleDeviceList(data);
  });

  deviceSocket.on('device-selected', (data) => {
    console.log('收到设备选择结果:', data);
    handleDeviceSelected(data);
  });

   deviceSocket.on('device-screenshot', (data) => {
    console.log('收到设备截图:', data);
    handleDeviceScreenshot(data);
  });
}

function handleDeviceList(data) {
  deviceLoading.value = false;

  if (!data || !data.success) {
    ElMessage.error(data?.error || '获取设备列表失败');
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
    ElMessage.error(data?.error || '连接设备失败');
    return;
  }

  currentDeviceId.value = data.currentDeviceId || '';

  if (currentDeviceId.value) {
    selectedDeviceId.value = currentDeviceId.value;
    ElMessage.success(`已连接设备: ${currentDeviceId.value}`);
  } else {
    ElMessage.info('已清除当前连接设备');
  }
}

function handleDeviceScreenshot(data) {
  screenshotLoading.value = false;

  if (!data || !data.success || !data.image) {
    ElMessage.error(data?.error || '获取截图失败');
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
        fileSize: '--',
        format: 'PNG',
        width: img.width,
        height: img.height,
      },
      selectedColors: [],
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
      type: 'get_devices'
    });
  } catch (error) {
    console.error('刷新设备失败:', error);
    ElMessage.error(`刷新设备失败: ${error.message || '未知错误'}`);
    deviceLoading.value = false;
  }
}

async function connectSelectedDevice() {
  if (!selectedDeviceId.value) return;
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'set_device',
      deviceId: selectedDeviceId.value
    });
  } catch (error) {
    console.error('连接设备失败:', error);
    ElMessage.error(`连接设备失败: ${error.message || '未知错误'}`);
  }
}

async function captureScreenshot() {
  if (!currentDeviceId.value) {
    ElMessage.warning('请先连接设备');
    return;
  }

  screenshotLoading.value = true;
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'capture_screenshot',
    });
  } catch (error) {
    console.error('截图失败:', error);
    ElMessage.error(`截图失败: ${error.message || '未知错误'}`);
    screenshotLoading.value = false;
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
        // 更新鼠标样式
        updateCursorStyle(imageX, imageY);
        
        // 正在拖动边框调整大小
        if (isResizing.value && selectionDisplay.value && resizeHandle.value) {
          updateSelectionRectsByResize(imageX, imageY, imageRect);
        }

        // 更新圈选时的矩形
        if (isSelecting.value && selectionStart.value) {
          selectionCurrent.value = {
            imageX,
            imageY,
            naturalX,
            naturalY,
          };
          updateSelectionRects();
        }

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
        containerCursor.value = 'crosshair';
      }
  } else {
    magnifierVisible.value = false;
    currentColor.value = null;
    containerCursor.value = 'crosshair';
  }
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
  containerCursor.value = 'crosshair';

  // 不清除 selectionDisplay / selectionRect，保证圈选框在滚动时仍然存在
  // 也不强制修改 isSelecting / isResizing，避免与正在进行的其它操作冲突
}

// 鼠标按下开始圈选
function handleMouseDown(event) {
  if (!currentImage.value || !imageRef.value) return;

  // 仅响应左键
  if (event.button !== 0) return;

  const imageRect = imageRef.value.getBoundingClientRect();
  const imageX = event.clientX - imageRect.left;
  const imageY = event.clientY - imageRect.top;

  if (imageX < 0 || imageY < 0 || imageX >= imageRect.width || imageY >= imageRect.height) {
    return;
  }

  // 如果已有选区，优先判断是否点击在边框附近，进入拖拉边框模式；
  // 如果没有点在边框上，则不允许重新开始圈选（必须先右键清除）
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
    // 有圈选但没点到边框上：禁止重新圈选
    return;
  }

  const scaleX = imageRef.value.naturalWidth / imageRect.width;
  const scaleY = imageRef.value.naturalHeight / imageRect.height;
  const naturalX = imageX * scaleX;
  const naturalY = imageY * scaleY;

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

// 鼠标抬起结束圈选
function handleMouseUp(event) {
  if (!imageRef.value) return;

  const imageRect = imageRef.value.getBoundingClientRect();
  const imageX = event.clientX - imageRect.left;
  const imageY = event.clientY - imageRect.top;

  const clampedX = Math.min(Math.max(imageX, 0), imageRect.width);
  const clampedY = Math.min(Math.max(imageY, 0), imageRect.height);

  const scaleX = imageRef.value.naturalWidth / imageRect.width;
  const scaleY = imageRef.value.naturalHeight / imageRect.height;
  const naturalX = clampedX * scaleX;
  const naturalY = clampedY * scaleY;

  if (isSelecting.value && selectionStart.value) {
    // 检查是否是真正的拖动（而不是点击）
    const dragThreshold = 5; // 拖动阈值，像素
    const dx = Math.abs(clampedX - selectionStart.value.imageX);
    const dy = Math.abs(clampedY - selectionStart.value.imageY);
    const dragDistance = Math.sqrt(dx * dx + dy * dy);

    if (dragDistance >= dragThreshold) {
      // 真正的拖动，且当前没有圈选框时，创建新的圈选框
      if (selectionDisplay.value || selectionRect.value) {
        // 已经有圈选框，则不再创建新的，直接返回
        selectionStart.value = null;
        selectionCurrent.value = null;
        isSelecting.value = false;
        return;
      }

      selectionCurrent.value = {
        imageX: clampedX,
        imageY: clampedY,
        naturalX,
        naturalY,
      };
      updateSelectionRects();
    } else {
      // 只是点击，不创建或清除圈选框，仅重置本次拖拽状态
      selectionStart.value = null;
      selectionCurrent.value = null;
    }
  }

  if (isResizing.value && selectionDisplay.value && selectionRect.value) {
    updateSelectionRectsByResize(clampedX, clampedY, imageRect);
  }

  isSelecting.value = false;
  isResizing.value = false;
  resizeHandle.value = null;
}

// 右键点击：清除圈选框
function handleRightClick() {
  if (selectionDisplay.value || selectionRect.value) {
    selectionDisplay.value = null;
    selectionRect.value = null;
    // 同时重置与圈选相关的状态，避免残留影响
    isSelecting.value = false;
    isResizing.value = false;
    selectionStart.value = null;
    selectionCurrent.value = null;
    resizeHandle.value = null;
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
}

// 圈选矩形样式（转换为 CSS 像素）
const selectionStyle = computed(() => {
  if (!selectionDisplay.value) return {};
  const rect = selectionDisplay.value;
  return {
    left: rect.x + 'px',
    top: rect.y + 'px',
    width: rect.w + 'px',
    height: rect.h + 'px',
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
  if (nearLeft && nearTop) return 'top-left';
  if (nearRight && nearTop) return 'top-right';
  if (nearLeft && nearBottom) return 'bottom-left';
  if (nearRight && nearBottom) return 'bottom-right';

  // 再判断边
  const withinVertical = y >= top - margin && y <= bottom + margin;
  const withinHorizontal = x >= left - margin && x <= right + margin;
  if (nearLeft && withinVertical) return 'left';
  if (nearRight && withinVertical) return 'right';
  if (nearTop && withinHorizontal) return 'top';
  if (nearBottom && withinHorizontal) return 'bottom';

  return null;
}

// 更新鼠标样式
function updateCursorStyle(imageX, imageY) {
  // 如果正在拖动边框，保持相应的 cursor 样式
  if (isResizing.value && resizeHandle.value) {
    const cursorMap = {
      'left': 'ew-resize',
      'right': 'ew-resize',
      'top': 'ns-resize',
      'bottom': 'ns-resize',
      'top-left': 'nw-resize',
      'top-right': 'ne-resize',
      'bottom-left': 'sw-resize',
      'bottom-right': 'se-resize'
    };
    containerCursor.value = cursorMap[resizeHandle.value] || 'crosshair';
    return;
  }

  // 如果正在圈选，使用 crosshair
  if (isSelecting.value) {
    containerCursor.value = 'crosshair';
    return;
  }

  // 如果有选区，检测鼠标是否在边框附近
  if (selectionDisplay.value) {
    const handle = getResizeHandleAtPoint(imageX, imageY, selectionDisplay.value);
    if (handle) {
      const cursorMap = {
        'left': 'ew-resize',
        'right': 'ew-resize',
        'top': 'ns-resize',
        'bottom': 'ns-resize',
        'top-left': 'nw-resize',
        'top-right': 'ne-resize',
        'bottom-left': 'sw-resize',
        'bottom-right': 'se-resize'
      };
      containerCursor.value = cursorMap[handle] || 'crosshair';
      return;
    }
  }

  // 默认样式
  containerCursor.value = 'crosshair';
}

// 根据拖动边框更新矩形（传入的是当前鼠标在图片显示坐标中的位置）
function updateSelectionRectsByResize(imageX, imageY, imageRect) {
  if (!selectionDisplay.value || !selectionRect.value || !imageRef.value || !resizeHandle.value) return;

  const scaleX = imageRef.value.naturalWidth / imageRect.width;
  const scaleY = imageRef.value.naturalHeight / imageRect.height;

  const disp = { ...selectionDisplay.value };
  const minSize = 3; // 最小宽高，避免为 0

  let left = disp.x;
  let top = disp.y;
  let right = disp.x + disp.w;
  let bottom = disp.y + disp.h;

  const handle = resizeHandle.value;

  // 限制拖动点在图片显示范围内
  const clampX = Math.min(Math.max(imageX, 0), imageRect.width);
  const clampY = Math.min(Math.max(imageY, 0), imageRect.height);

  if (handle.includes('left')) {
    left = Math.min(clampX, right - minSize);
  } else if (handle.includes('right')) {
    right = Math.max(clampX, left + minSize);
  }

  if (handle.includes('top')) {
    top = Math.min(clampY, bottom - minSize);
  } else if (handle.includes('bottom')) {
    bottom = Math.max(clampY, top + minSize);
  }

  // 单独水平或垂直边（防止只含单词时遗漏）
  if (handle === 'left') {
    left = Math.min(clampX, right - minSize);
  }
  if (handle === 'right') {
    right = Math.max(clampX, left + minSize);
  }
  if (handle === 'top') {
    top = Math.min(clampY, bottom - minSize);
  }
  if (handle === 'bottom') {
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
  const natX = Math.floor(Math.max(0, left * scaleX));
  const natY = Math.floor(Math.max(0, top * scaleY));
  const natW = Math.floor(newW * scaleX);
  const natH = Math.floor(newH * scaleY);

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
  // 切换图片时清空圈选信息
  isSelecting.value = false;
  isResizing.value = false;
  selectionStart.value = null;
  selectionCurrent.value = null;
  selectionDisplay.value = null;
  selectionRect.value = null;
  resizeHandle.value = null;
  containerCursor.value = 'crosshair';
}

// 监听当前图片切换，重置放大镜和颜色
watch(currentImageIndex, () => {
  magnifierVisible.value = false;
  currentColor.value = null;
  currentPosition.value = { x: 0, y: 0 };
  isSelecting.value = false;
  isResizing.value = false;
  resizeHandle.value = null;
  containerCursor.value = 'crosshair';
  
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

onUnmounted(() => {
  if (deviceSocket) {
    deviceSocket.disconnect();
    deviceSocket = null;
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
  user-select: none;
  flex-shrink: 0;
  box-sizing: border-box;
}

.image-wrapper {
  display: inline-block;
  position: relative;
}

/* 圈选矩形样式 */
.selection-rect {
  position: absolute;
  border: 2px solid #22c55e;
  background: rgba(34, 197, 94, 0.2);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.4);
  pointer-events: none;
  box-sizing: border-box;
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

