<template>
  <div class="image-match-debug">
    <el-form size="small">
      <el-form-item label="小图">
        <div class="image-upload-area">
          <input ref="smallImageInputRef" type="file" accept="image/*" style="display: none"
            @change="handleSmallImageSelect" />
          <div v-if="smallImageUrl" class="image-preview">
            <el-image :src="smallImageUrl" :preview-src-list="[smallImageUrl]" fit="contain" preview-teleported
              class="thumbnail-image" />
            <el-button type="danger" size="small" circle class="remove-btn" @click="clearSmallImage">
              <el-icon>
                <Close />
              </el-icon>
            </el-button>
          </div>
          <div v-else>
            <div style="color: #909399; font-size: 12px;">不传,默认透明图</div>
            <div class="button-group">
              <el-button type="primary" size="small" @click="smallImageInputRef?.click()">
                上传小图
              </el-button>
              <el-button type="success" size="small" :disabled="!transparentImageUrl" @click="useTransparentImage">
                加入透明图
              </el-button>
            </div>
          </div>
        </div>
      </el-form-item>
      <el-form-item label="大图">
        <div class="image-upload-area">
          <input ref="largeImageInputRef" type="file" accept="image/*" style="display: none"
            @change="handleLargeImageSelect" />
          <div v-if="largeImageUrl" class="image-preview">
            <el-image :src="largeImageUrl" :preview-src-list="[largeImageUrl]" fit="contain" preview-teleported
              class="thumbnail-image" />
            <el-button type="danger" size="small" circle class="remove-btn" @click="clearLargeImage">
              <el-icon>
                <Close />
              </el-icon>
            </el-button>
          </div>
          <div v-else>
            <div style="color: #909399;font-size: 12px;">不传,默认截图</div>
            <div class="button-group">
              <el-button type="primary" size="small" @click="largeImageInputRef?.click()">
                上传大图
              </el-button>
              <el-button type="success" size="small" :loading="screenshotLoading" :disabled="!currentDeviceId"
                @click="handleScreenshotClick">
                截图
              </el-button>
            </div>
          </div>
        </div>
      </el-form-item>
      <el-form-item label="范围">
        <el-input v-model="regionInput" placeholder="例如: 0,0,100,100 (留空则查询全图) (x,y,w,h)" size="small" clearable />
      </el-form-item>
      <el-form-item label="偏色">
        <el-input
          v-model="colorToleranceInput"
          placeholder="例如: C9C0B2-25211F|111111-222222 (多个用|分割)"
          size="small"
          clearable
        >
          <template #append>
            <el-button @click="handleGetDeviation">获取偏色</el-button>
          </template>
        </el-input>
      </el-form-item>
    </el-form>

    <el-button type="primary" size="small" :loading="matching"
      :disabled="(!smallImageUrl && !transparentImageUrl) || (!largeImageUrl && !currentDeviceId)" @click="handleMatch"
      style="width: 100%; margin-bottom: 5px;">
      {{ matching ? "匹配中..." : "开始匹配" }}
    </el-button>

    <div class="result-section">
      <el-image :src="resultImageUrl" :preview-src-list="[resultImageUrl]" fit="contain" preview-teleported
        style="height: 100%; width: 100%;">
        <template #placeholder>
          <div style="display: flex;justify-content: center;align-items: center;height: 100%;width: 100%;">匹配结果将显示在此处
          </div>
        </template>
      </el-image>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import { Close } from "@element-plus/icons-vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
import ImageDisplayArea from "../common/ImageDisplayArea.vue";

const props = defineProps({
  transparentImageUrl: {
    type: String,
    default: null,
  },
  currentDeviceId: {
    type: String,
    default: "",
  },
  // 从右侧“偏色计算”标签页传入的已选偏色列表
  selectedDeviations: {
    type: Array,
    default: () => [],
  },
});

const smallImageInputRef = ref(null);
const largeImageInputRef = ref(null);
const smallImageUrl = ref(null);
const largeImageUrl = ref(null);
const smallImageFile = ref(null);
const largeImageFile = ref(null);
const regionInput = ref("");
const colorToleranceInput = ref("");
const matching = ref(false);
const resultImageUrl = ref(null);
const matchResult = ref(null);
const screenshotLoading = ref(false);
const isScreenshotPending = ref(false);
let matchSocket = null;

// 获取偏色（与 CodeGeneratorTab 中行为保持一致）
function handleGetDeviation() {
  if (!props.selectedDeviations || props.selectedDeviations.length === 0) {
    ElMessage.warning(`请先在"偏色计算"标签页中选择偏色`);
    return;
  }

  // 将选中的偏色用 | 连接
  const deviationStr = props.selectedDeviations.join("|");
  colorToleranceInput.value = deviationStr;
  ElMessage.success(`已获取 ${props.selectedDeviations.length} 个偏色`);
}

// 初始化 Socket 连接
function initMatchSocket() {
  if (matchSocket) {
    return;
  }

  matchSocket = io("ws://localhost:7070");

  matchSocket.on("connect", () => {
    console.log("匹配 Socket 连接成功");
  });

  matchSocket.on("image-match-result", (data) => {
    console.log("收到匹配结果:", data);
    handleMatchResult(data);
  });

  matchSocket.on("device-screenshot", (data) => {
    console.log("收到设备截图 (ImageMatchDebug):", data);
    // 只处理自己发起的截图请求
    if (isScreenshotPending.value) {
      handleDeviceScreenshot(data);
    }
  });
}

// 处理小图选择
function handleSmallImageSelect(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  if (!file.type.startsWith("image/")) {
    ElMessage.error("请选择图片文件");
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    smallImageUrl.value = e.target.result;
    smallImageFile.value = file;
  };
  reader.readAsDataURL(file);
}

// 处理大图选择
function handleLargeImageSelect(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  if (!file.type.startsWith("image/")) {
    ElMessage.error("请选择图片文件");
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    largeImageUrl.value = e.target.result;
    largeImageFile.value = file;
  };
  reader.readAsDataURL(file);
}

// 清空小图
function clearSmallImage() {
  smallImageUrl.value = null;
  smallImageFile.value = null;
  if (smallImageInputRef.value) {
    smallImageInputRef.value.value = "";
  }
}

// 清空大图
function clearLargeImage() {
  largeImageUrl.value = null;
  largeImageFile.value = null;
  if (largeImageInputRef.value) {
    largeImageInputRef.value.value = "";
  }
}

// 使用透明图作为小图
function useTransparentImage() {
  if (!props.transparentImageUrl) {
    ElMessage.warning("当前没有透明图");
    return;
  }

  // 将透明图 URL 设置为小图
  smallImageUrl.value = props.transparentImageUrl;
  smallImageFile.value = null; // 透明图没有文件对象

  ElMessage.success("已加入透明图");
}

// 处理截图按钮点击
async function handleScreenshotClick() {
  // 检查是否有当前设备
  if (!props.currentDeviceId) {
    ElMessage.warning("请先连接设备");
    return;
  }

  screenshotLoading.value = true;
  isScreenshotPending.value = true;

  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "capture_screenshot",
      source: "image-match-debug", // 添加来源标识
    });
    // 截图结果会通过 socket 事件返回，在 handleDeviceScreenshot 中处理
    // 设置超时，防止标志一直存在
    setTimeout(() => {
      if (isScreenshotPending.value) {
        isScreenshotPending.value = false;
        screenshotLoading.value = false;
        ElMessage.error("截图超时");
      }
    }, 10000); // 10秒超时
  } catch (error) {
    console.error("截图失败:", error);
    ElMessage.error(`截图失败: ${error.message || "未知错误"}`);
    screenshotLoading.value = false;
    isScreenshotPending.value = false;
  }
}

// 处理设备截图结果
function handleDeviceScreenshot(data) {
  screenshotLoading.value = false;
  isScreenshotPending.value = false;

  if (!data || !data.success || !data.image) {
    ElMessage.error(data?.error || "获取截图失败");
    return;
  }

  // 将截图设置为大图
  const url = `data:image/png;base64,${data.image}`;
  largeImageUrl.value = url;
  largeImageFile.value = null; // 截图没有文件对象

  ElMessage.success("截图已设置为大图");
}

// 处理匹配
async function handleMatch() {
  // 检查是否有小图或透明图
  if (!smallImageFile.value && !smallImageUrl.value && !props.transparentImageUrl) {
    ElMessage.warning("请先上传小图或使用透明图");
    return;
  }

  // 检查是否有大图或设备ID（用于自动截图）
  if (!largeImageFile.value && !largeImageUrl.value && !props.currentDeviceId) {
    ElMessage.warning("请先上传大图或连接设备以自动截图");
    return;
  }

  matching.value = true;
  resultImageUrl.value = null;
  matchResult.value = null;

  try {
    // 读取小图为 base64
    let smallBase64 = null;
    if (smallImageFile.value) {
      // 从文件读取
      smallBase64 = await fileToBase64(smallImageFile.value);
    } else if (smallImageUrl.value) {
      // 从 URL 中提取 base64（已上传的小图）
      const base64Data = smallImageUrl.value.split(",")[1];
      if (base64Data) {
        smallBase64 = base64Data;
      }
    } else if (props.transparentImageUrl) {
      // 使用透明图作为小图
      const base64Data = props.transparentImageUrl.split(",")[1];
      if (base64Data) {
        smallBase64 = base64Data;
      }
    }

    if (!smallBase64) {
      ElMessage.error("无法获取小图数据");
      matching.value = false;
      return;
    }

    // 读取大图为 base64（如果没有大图，则不传，让后端自动截图）
    let largeBase64 = null;
    if (largeImageFile.value) {
      // 从文件读取
      largeBase64 = await fileToBase64(largeImageFile.value);
    } else if (largeImageUrl.value) {
      // 从 URL 中提取 base64（截图的情况）
      const base64Data = largeImageUrl.value.split(",")[1];
      if (base64Data) {
        largeBase64 = base64Data;
      }
    }
    // 如果没有大图，largeBase64 保持为 null，后端会自动截图

    // 解析区域
    let region = null;
    if (regionInput.value.trim()) {
      const parts = regionInput.value.split(",").map((s) => s.trim());
      if (parts.length === 4) {
        const x = parseInt(parts[0]);
        const y = parseInt(parts[1]);
        const w = parseInt(parts[2]);
        const h = parseInt(parts[3]);
        if (!isNaN(x) && !isNaN(y) && !isNaN(w) && !isNaN(h)) {
          region = { x, y, w, h };
        }
      }
      if (!region) {
        ElMessage.warning("区域格式错误，将查询全图");
      }
    }

    // 解析偏色
    let colorTolerance = null;
    if (colorToleranceInput.value.trim()) {
      const parts = colorToleranceInput.value.split("|").map((s) => s.trim());
      if (parts.length > 0 && parts.every((p) => p.includes("-"))) {
        colorTolerance = parts;
      } else {
        ElMessage.warning("偏色格式错误，将使用普通找图");
      }
    }

    // 发送匹配请求
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "image_match",
      smallImage: smallBase64,
      largeImage: largeBase64, // 如果为 null，后端会自动截图
      region: region,
      colorTolerance: colorTolerance,
    });

    // 设置超时
    setTimeout(() => {
      if (matching.value) {
        matching.value = false;
        ElMessage.error("匹配超时");
      }
    }, 30000); // 30秒超时
  } catch (error) {
    console.error("匹配失败:", error);
    ElMessage.error(`匹配失败: ${error.message || "未知错误"}`);
    matching.value = false;
  }
}

// 处理匹配结果
function handleMatchResult(data) {
  matching.value = false;

  if (!data || !data.success) {
    ElMessage.error(data?.error || "匹配失败");
    return;
  }

  if (data.resultImage) {
    resultImageUrl.value = `data:image/png;base64,${data.resultImage}`;
  }

  if (data.result) {
    matchResult.value = data.result;
    ElMessage.success("匹配完成");
  } else {
    ElMessage.warning("未找到匹配位置");
  }
}

// 文件转 base64
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      // 移除 data:image/...;base64, 前缀
      const base64 = e.target.result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// 组件挂载时初始化 socket
onMounted(() => {
  initMatchSocket();
});

// 组件卸载时断开 socket
onUnmounted(() => {
  if (matchSocket) {
    matchSocket.disconnect();
    matchSocket = null;
  }
});
</script>

<style scoped>
.image-match-debug {
  display: flex;
  flex-direction: column;
  height: 590px;
  overflow-y: auto;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
}

.image-upload-area {
  height: 80px;
  width: 100%;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.image-preview {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail-image {
  height: 80px;
  object-fit: contain;
}

.remove-btn {
  position: absolute;
  top: 5px;
  right: 5px;
}

.result-section {
  flex: 1;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  /* gap: 5px; */
  /* 深色棋盘格背景，用于显示透明区域 */
  background: #1a1a2e;
  background-image: linear-gradient(45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(-45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #2a2a3e 75%),
    linear-gradient(-45deg, transparent 75%, #2a2a3e 75%);
  background-size: 16px 16px;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
  color: #909399;
  font-size: 12px;
}

.button-group {
  display: flex;
  gap: 5px;
  width: 100%;
}

.button-group .el-button {
  flex: 1;
}

.el-form-item {
  margin-bottom: 5px;
}
</style>
