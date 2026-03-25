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
    <el-tabs
      type="border-card"
      size="mini"
      v-model="activeTab"
      @tab-change="handleTabChange"
    >
    <el-tab-pane label="配置" name="config">
        <ConfigTab
          :current-image="currentImage"
          :selection-rect="selectionRect"
          :font-library-list="fontLibraryList"
          :current-device-id="currentDeviceId"
          ref="configTabRef"
          @add-font-library="handleAddFontLibrary"
          @add-image-to-library="handleAddImageToLibrary"
          @delete-library-resource="handleDeleteLibraryResource"
          @open-image-test="handleOpenImageTest"
          @start-code-generator-selection="
            (type) => $emit('start-code-generator-selection', type)
          "
          @stop-code-generator-selection="$emit('stop-code-generator-selection')"
        />
      </el-tab-pane>
      <el-tab-pane label="字库">
        <FontLibraryTab ref="fontLibraryTabRef" :current-device-id="currentDeviceId" />
      </el-tab-pane>
      <el-tab-pane label="图片库" name="image-library">
        <ImageLibraryTab :current-device-id="currentDeviceId" ref="imageLibraryTabRef" />
      </el-tab-pane>
      <!-- <el-tab-pane label="偏色二值化" name="deviation">
        <ColorSelectionTab
          :current-selected-colors="currentSelectedColors"
          :current-image="currentImage"
          :selection-rect="selectionRect"
          :has-font-library-file="hasFontLibraryFile"
          @remove-color="$emit('remove-color', $event)"
          @clear-all-colors="$emit('clear-all-colors')"
          @add-colors="$emit('add-colors', $event)"
          @add-font-library="handleAddFontLibrary"
          @start-code-generator-selection="
            (type) => $emit('start-code-generator-selection', type)
          "
          @stop-code-generator-selection="$emit('stop-code-generator-selection')"
          ref="colorSelectionTabRef"
        />
      </el-tab-pane>

      <el-tab-pane label="找字测试">
        <FontLibraryMatchDebug
          :current-device-id="currentDeviceId"
          :font-library-list="fontLibraryList"
        />
      </el-tab-pane>
      <el-tab-pane label="识字测试">
        <FontLibraryOcrTest
          :current-device-id="currentDeviceId"
          :font-library-path="fontLibraryPath"
        />
      </el-tab-pane> -->

      <!-- <el-tab-pane label="颜色记录" name="color-record">
        <ColorRecordList 
          :colors="recordedColors"
          @remove-color="$emit('remove-record-color', $event)"
          @clear-all-colors="$emit('clear-all-record-colors')"
        />
      </el-tab-pane> -->
      <!-- <el-tab-pane label="透明图制作">
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
      </el-tab-pane> -->

      <!-- <el-tab-pane label="代码">
        <CodeGeneratorTab 
          :selected-deviations="selectedDeviations"
          :selection-rect="selectionRect"
          :transparent-image-url="transparentImageUrl"
          :current-image-url="currentImage?.url || null"
          @start-code-generator-selection="(type) => $emit('start-code-generator-selection', type)"
          @stop-code-generator-selection="$emit('stop-code-generator-selection')"
          ref="codeGeneratorTabRef"
        />
      </el-tab-pane> -->
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
import ColorRecordList from "../lists/ColorRecordList.vue";
import FontLibraryTab from "../tabs/FontLibraryTab.vue";
import FontLibraryMatchDebug from "../tabs/FontLibraryMatchDebug.vue";
import FontLibraryOcrTest from "../tabs/FontLibraryOcrTest.vue";
import ConfigTab from "../tabs/ConfigTab.vue";
import ImageLibraryTab from "../tabs/ImageLibraryTab.vue";
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
  recordedColors: {
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
  "add-colors",
  "remove-record-color",
  "clear-all-record-colors",
  "tab-change",
  "right-panel-screenshot-start",
  "right-panel-screenshot-end",
  "start-code-generator-selection",
  "stop-code-generator-selection",
]);

const magnifierCardRef = ref(null);
const colorSelectionTabRef = ref(null);
const imageUploadTabRef = ref(null);
const codeGeneratorTabRef = ref(null);
const fontLibraryTabRef = ref(null);
const imageLibraryTabRef = ref(null);
const configTabRef = ref(null);
const uploadedImages = ref([]);
const screenshotLoading = ref(false);
const isRightPanelScreenshotPending = ref(false); // 标记是否是右侧面板发起的截图
const activeTab = ref("config"); // 当前激活的 tab
let deviceSocket = null;

// 处理 tab 切换
const handleTabChange = (tabName) => {
  activeTab.value = tabName;
  emit("tab-change", tabName);
  // 切换到偏色二值化 tab 时刷新配置数据，使级联选项与 ConfigTab 中最新配置一致
  if (tabName === "deviation" && colorSelectionTabRef.value?.refreshConfig) {
    colorSelectionTabRef.value.refreshConfig();
  }
};

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

// 检查是否有字库文件
const hasFontLibraryFile = computed(() => {
  if (fontLibraryTabRef.value) {
    return fontLibraryTabRef.value.hasSelectedFile?.() || false;
  }
  return false;
});

// 获取字库列表
const fontLibraryList = computed(() => {
  if (fontLibraryTabRef.value) {
    return fontLibraryTabRef.value.getFontLibraryList?.() || [];
  }
  return [];
});

// 获取字库路径（字库 tab 中选择的字库文件路径，供识字测试使用）
const fontLibraryPath = computed(() => {
  if (fontLibraryTabRef.value) {
    return fontLibraryTabRef.value.getFontLibraryPath?.() || "";
  }
  return "";
});

// 获取处理后的图片 URL（从 ColorSelectionTab 组件）
const processedImageUrl = computed(() => {
  if (colorSelectionTabRef.value) {
    return colorSelectionTabRef.value.getProcessedImageUrl?.() || null;
  }
  return null;
});

// 处理图片更新
const handleImagesUpdated = async (newImages) => {
  uploadedImages.value.push(...newImages);
  // 图片更新后，自动调用制作透明图（静默模式）
  await nextTick();
  if (imageUploadTabRef.value && uploadedImages.value.length > 0) {
    imageUploadTabRef.value.makeTransparentImage?.(true);
  }
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
async function handleDeviceScreenshot(data) {
  screenshotLoading.value = false;
  isRightPanelScreenshotPending.value = false; // 清除标志
  emit("right-panel-screenshot-end"); // 通知父组件截图结束

  if (!data || !data.success || !data.image) {
    ElMessage.error(data?.error || "获取截图失败");
    return;
  }

  const url = `data:image/png;base64,${data.image}`;
  const img = new Image();
  img.onload = async () => {
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

    // 截图完成后，自动调用制作透明图（静默模式）
    await nextTick();
    if (imageUploadTabRef.value && uploadedImages.value.length > 0) {
      imageUploadTabRef.value.makeTransparentImage?.(true);
    }
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
  getColorSelectionTabRef: () => colorSelectionTabRef.value,
  getConfigTabRef: () => configTabRef.value,
  getImageLibraryTabRef: () => imageLibraryTabRef.value,
});

// 组件挂载时初始化 socket，并同步当前 tab 到父组件（避免父组件 activeRightTab 仍为默认值导致选色落入错误列表）
onMounted(() => {
  initDeviceSocket();
  emit("tab-change", activeTab.value);
});

// 处理添加字库
const handleAddFontLibrary = async (fontItem, resolveCallback) => {
  // 检查是否已选择字库文件
  if (fontLibraryTabRef.value) {
    const hasFile = fontLibraryTabRef.value.hasSelectedFile?.();
    if (!hasFile) {
      ElMessage.warning("请先在字库标签页中选择字库 JSON 文件");
      if (resolveCallback) resolveCallback(false);
      return false;
    }
    // 将字库数据传递给 FontLibraryTab，并等待结果
    // 成功或失败的消息已在 FontLibraryTab 中显示，这里不再显示额外消息
    const success = await fontLibraryTabRef.value.addFontLibraryItem?.(fontItem);
    const result = success === true; // 确保只有 true 才返回 true，其他情况都返回 false
    if (resolveCallback) resolveCallback(result);
    return result;
  }
  if (resolveCallback) resolveCallback(false);
  return false;
};

// 组件卸载时断开 socket
onUnmounted(() => {
  if (deviceSocket) {
    deviceSocket.disconnect();
    deviceSocket = null;
  }
});

// 处理从 ConfigTab 发起的“图片测试”：用图片库中与 testFontLibraryName 同名的图片打开模板匹配测试
const handleOpenImageTest = ({ name, similarity, region } = {}) => {
  // 只有在确实找到同名图片时，才切换到“图片库”tab
  // 未找到时由 ImageLibraryTab 内部弹消息（不做 tab 跳转）
  const opened = imageLibraryTabRef.value?.openTestByImageName?.(name, {
    similarity,
    region,
  });
  if (opened === true) {
    activeTab.value = "image-library";
  }
};

// 处理从 ConfigTab 发起的“删除配置项对应资源”（图片库或字库中同名资源）
const handleDeleteLibraryResource = async ({ type, name } = {}) => {
  if (!name) return;
  if (type === "图片") {
    const deleted = imageLibraryTabRef.value?.deleteByName?.(name);
    if (!deleted) {
      ElMessage.info("图片库中未找到同名资源，或已删除");
    }
  } else if (type === "点阵") {
    try {
      const deleted = await fontLibraryTabRef.value?.deleteByName?.(name);
      if (!deleted) {
        ElMessage.info("字库中未找到同名资源，或已删除");
      }
    } catch (e) {
      ElMessage.error("删除字库资源失败: " + (e?.message || "未知错误"));
    }
  }
};

// 处理从 ConfigTab 发起的“添加图片到图片库”请求
const handleAddImageToLibrary = async (payload) => {
  try {
    const { name, selectionRect, currentImageUrl } = payload || {};
    if (!currentImageUrl) {
      ElMessage.warning("当前没有图片，无法添加到图片库");
      return;
    }

    const npzPath = imageLibraryTabRef.value?.getNpzPath?.() || "";
    if (!npzPath) {
      ElMessage.warning("请先在图片库标签页中选择 .npz 图片库文件");
      return;
    }

    await new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = async () => {
        try {
          let startX = 0;
          let startY = 0;
          let width = img.width;
          let height = img.height;

          if (selectionRect && selectionRect.w > 0 && selectionRect.h > 0) {
            startX = Math.max(0, Math.min(selectionRect.x, img.width - 1));
            startY = Math.max(0, Math.min(selectionRect.y, img.height - 1));
            width = Math.min(selectionRect.w, img.width - startX);
            height = Math.min(selectionRect.h, img.height - startY);
          }

          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");
          canvas.width = width;
          canvas.height = height;
          ctx.drawImage(
            img,
            startX,
            startY,
            width,
            height,
            0,
            0,
            width,
            height
          );
          const dataUrl = canvas.toDataURL("image/png");
          const base64 =
            dataUrl.indexOf(",") >= 0 ? dataUrl.split(",")[1] : dataUrl;

          const added = await imageLibraryTabRef.value?.addImageItemFromConfig?.({
            name,
            width,
            height,
            base64,
          });
          if (added) {
            ElMessage.success("已添加到图片库列表，稍后将自动同步到 .npz 文件");
          // 主动触发一次同步，避免初始化阶段的防抖/标志导致本次添加未写入 .npz
          try {
            await imageLibraryTabRef.value?.syncNow?.();
          } catch (e) {
            console.error("手动同步图片库到 .npz 失败:", e);
          }
          }
          resolve();
        } catch (e) {
          reject(e);
        }
      };
      img.onerror = (e) => {
        reject(e);
      };
      img.src = currentImageUrl;
    });
  } catch (error) {
    console.error("添加图片到图片库失败:", error);
    // 这里的错误提示已经在内部处理，大多数情况下不需要重复提示
  }
};
</script>

<style scoped>
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
  padding: 6px 8px;
  width: 460px;
  min-width: 460px;
  max-width: 460px;
  height: 882px;
  overflow: hidden;
  box-sizing: border-box;
  background: #f8fafc;
}

/* 放大镜卡片不允许被压缩 */
.right-panel > :first-child {
  flex-shrink: 0;
}

/* Tabs 容器填满剩余高度 */
.right-panel > .el-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Tab 整体边框 */
.el-tabs :deep(.el-tabs--border-card) {
  border-color: #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

/* Tab 头部美化 */
.el-tabs :deep(.el-tabs__header) {
  flex-shrink: 0;
  margin-bottom: 0;
  background: linear-gradient(180deg, #f8fafc, #f1f5f9);
  border-bottom: 1px solid #e2e8f0;
}

.el-tabs :deep(.el-tabs__item) {
  font-size: 12px;
  font-weight: 500;
  padding: 0 18px;
  height: 34px;
  line-height: 34px;
  color: #64748b;
  transition: color 0.2s, font-weight 0.2s;
  border-right: 1px solid #e8ecf1;
}

.el-tabs :deep(.el-tabs__item:last-child) {
  border-right: none;
}

.el-tabs :deep(.el-tabs__item:hover) {
  color: #475569;
}

.el-tabs :deep(.el-tabs__item.is-active) {
  font-weight: 600;
  color: #6366f1;
  background: #fff;
}

.el-tabs :deep(.el-tabs__content) {
  padding: 6px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  background: #fff;
}

.el-tabs :deep(.el-tab-pane) {
  height: 100%;
}
</style>
