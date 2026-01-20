<template>
  <div class="right-panel">
    <!-- 放大镜 -->
    <MagnifierCard
      :magnifier-visible="magnifierVisible"
      :current-image="currentImage"
      :current-position="currentPosition"
      :current-color="currentColor"
      ref="magnifierCardRef"
    />

    <!-- 选中颜色列表 -->
    <el-tabs type="border-card" size="mini">
      <el-tab-pane label="偏色计算">
        <ColorSelectionTab
          :current-selected-colors="currentSelectedColors"
          :current-image="currentImage"
          :selection-rect="selectionRect"
          @remove-color="$emit('remove-color', $event)"
          @clear-all-colors="$emit('clear-all-colors')"
          ref="colorSelectionTabRef"
        />
      </el-tab-pane>
      <el-tab-pane label="透明图制作">
        <ImageUploadTab
          :uploaded-images="uploadedImages"
          :screenshot-loading="screenshotLoading"
          :selected-deviations="selectedDeviations"
          :selection-rect="selectionRect"
          @screenshot-click="handleScreenshotClick"
          @images-updated="handleImagesUpdated"
          @remove-image="handleRemoveImage"
          @clear-all-images="handleClearAllImages"
          ref="imageUploadTabRef"
        />
      </el-tab-pane>
      <el-tab-pane label="调试图片">
        <ImageMatchDebug 
          :transparent-image-url="transparentImageUrl"
          :current-device-id="currentDeviceId"
        />
      </el-tab-pane>
      <el-tab-pane label="生成代码">
        <CodeGeneratorTab 
          :selected-deviations="selectedDeviations"
          :selection-rect="selectionRect"
          :transparent-image-url="transparentImageUrl"
          :current-image-url="currentImage?.url || null"
          @start-code-generator-selection="(type) => $emit('start-code-generator-selection', type)"
          @stop-code-generator-selection="$emit('stop-code-generator-selection')"
          ref="codeGeneratorTabRef"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from "vue";
import { ElMessage } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
import MagnifierCard from "../cards/MagnifierCard.vue";
import ColorSelectionTab from "../tabs/ColorSelectionTab.vue";
import ImageUploadTab from "../tabs/ImageUploadTab.vue";
import ImageMatchDebug from "../tabs/ImageMatchDebug.vue";
import CodeGeneratorTab from "../tabs/CodeGeneratorTab.vue";

const props = defineProps({
  magnifierVisible: {
    type: Boolean,
    default: false,
  },
  currentImage: {
    type: Object,
    default: null,
  },
  currentPosition: {
    type: Object,
    default: () => ({ x: 0, y: 0 }),
  },
  currentColor: {
    type: Object,
    default: null,
  },
  currentSelectedColors: {
    type: Array,
    default: () => [],
  },
  selectionRect: {
    type: Object,
    default: null,
  },
  imageRef: {
    type: Object,
    default: null,
  },
  currentDeviceId: {
    type: String,
    default: "",
  },
});

const emit = defineEmits([
  "remove-color", 
  "clear-all-colors", 
  "right-panel-screenshot-start", 
  "right-panel-screenshot-end",
  "start-code-generator-selection",
  "stop-code-generator-selection"
]);

const magnifierCardRef = ref(null);
const colorSelectionTabRef = ref(null);
const imageUploadTabRef = ref(null);
const codeGeneratorTabRef = ref(null);
const uploadedImages = ref([]);
const screenshotLoading = ref(false);
const isRightPanelScreenshotPending = ref(false); // 标记是否是右侧面板发起的截图
let deviceSocket = null;

// 获取透明图 URL
const transparentImageUrl = computed(() => {
  if (imageUploadTabRef.value) {
    return imageUploadTabRef.value.getTransparentImageUrl?.() || null;
  }
  return null;
});

// 获取选中的偏色列表（从 ColorSelectionTab 组件）
const selectedDeviations = computed(() => {
  if (colorSelectionTabRef.value) {
    return colorSelectionTabRef.value.getSelectedDeviations() || [];
  }
  return [];
});

// 处理图片更新
const handleImagesUpdated = (newImages) => {
  uploadedImages.value.push(...newImages);
};

// 删除图片
const handleRemoveImage = (index) => {
  uploadedImages.value.splice(index, 1);
  ElMessage.success("图片已删除");
};

// 清空所有图片
const handleClearAllImages = () => {
  if (uploadedImages.value.length === 0) {
    ElMessage.warning("列表已为空");
    return;
  }
  uploadedImages.value = [];
  ElMessage.success("已清空所有图片");
};

// 初始化设备 Socket 连接
function initDeviceSocket() {
  if (deviceSocket) {
    return; // 已经连接过了
  }

  deviceSocket = io("ws://localhost:7070");

  deviceSocket.on("connect", () => {
    console.log("设备 Socket 连接成功 (RightPanel)");
  });

  deviceSocket.on("device-screenshot", (data) => {
    console.log("收到设备截图 (RightPanel):", data);
    // 只处理自己发起的截图请求
    if (isRightPanelScreenshotPending.value) {
      handleDeviceScreenshot(data);
    }
  });
}

// 处理设备截图结果
function handleDeviceScreenshot(data) {
  screenshotLoading.value = false;
  isRightPanelScreenshotPending.value = false; // 清除标志
  emit("right-panel-screenshot-end"); // 通知父组件截图结束

  if (!data || !data.success || !data.image) {
    ElMessage.error(data?.error || "获取截图失败");
    return;
  }

  const url = `data:image/png;base64,${data.image}`;
  const img = new Image();
  img.onload = () => {
    // 创建缩略图
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

    // 添加到图片列表
    uploadedImages.value.push({
      id: Date.now() + Math.random(), // 生成唯一ID
      url: url,
      thumbnail: thumbnail,
      file: null, // 截图没有文件对象
    });

    ElMessage.success("截图已添加到图片列表");
  };
  img.onerror = () => {
    ElMessage.error("图片加载失败");
  };
  img.src = url;
}

// 处理截图按钮点击
async function handleScreenshotClick() {
  // 检查是否有当前设备
  if (!props.currentDeviceId) {
    ElMessage.warning("请先连接设备");
    return;
  }

  screenshotLoading.value = true;
  isRightPanelScreenshotPending.value = true; // 设置标志，表示这是右侧面板发起的截图
  // 先同步设置父组件的标志，确保在 socket 事件到达前已设置
  emit("right-panel-screenshot-start"); // 通知父组件开始截图
  // 使用 nextTick 确保 emit 事件已处理
  await nextTick();
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "capture_screenshot",
      source: "right-panel", // 添加来源标识
    });
    // 截图结果会通过 socket 事件返回，在 handleDeviceScreenshot 中处理
    // 设置超时，防止标志一直存在
    setTimeout(() => {
      if (isRightPanelScreenshotPending.value) {
        isRightPanelScreenshotPending.value = false;
        screenshotLoading.value = false;
        emit("right-panel-screenshot-end"); // 通知父组件截图结束
      }
    }, 10000); // 10秒超时
  } catch (error) {
    console.error("截图失败:", error);
    ElMessage.error(`截图失败: ${error.message || "未知错误"}`);
    screenshotLoading.value = false;
    isRightPanelScreenshotPending.value = false; // 清除标志
    emit("right-panel-screenshot-end"); // 通知父组件截图结束
  }
}

// 暴露放大镜 canvas 给父组件，用于绘制
// 同时暴露截图状态，让父组件可以检查
defineExpose({
  getMagnifierCanvas: () => magnifierCardRef.value?.getMagnifierCanvas(),
  get isRightPanelScreenshotPending() {
    return isRightPanelScreenshotPending.value;
  },
  getCodeGeneratorTabRef: () => codeGeneratorTabRef.value,
});

// 组件挂载时初始化 socket
onMounted(() => {
  initDeviceSocket();
});

// 组件卸载时断开 socket
onUnmounted(() => {
  if (deviceSocket) {
    deviceSocket.disconnect();
    deviceSocket = null;
  }
});
</script>

<style scoped>
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex-shrink: 0;
  padding: 0 5px;
  width: 460px;
}
.el-tabs :deep(.el-tabs__content) {
  padding: 2px;
  display: none !important; /* 隐藏默认的 tab-pane 内容，因为我们使用 router-view */
}

</style>
