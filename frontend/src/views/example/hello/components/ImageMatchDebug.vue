<template>
  <div class="image-match-debug">
    <div class="debug-section">
      <div class="section-title">小图</div>
      <div class="image-upload-area">
        <input
          ref="smallImageInputRef"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleSmallImageSelect"
        />
        <div v-if="smallImageUrl" class="image-preview">
          <img :src="smallImageUrl" alt="小图" />
          <el-button
            type="danger"
            size="small"
            circle
            class="remove-btn"
            @click="clearSmallImage"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div v-else class="button-group">
          <el-button
            type="primary"
            size="small"
            @click="smallImageInputRef?.click()"
          >
            上传小图
          </el-button>
          <el-button
            type="success"
            size="small"
            :disabled="!transparentImageUrl"
            @click="useTransparentImage"
          >
            加入透明图
          </el-button>
        </div>
      </div>
    </div>

    <div class="debug-section">
      <div class="section-title">大图</div>
      <div class="image-upload-area">
        <input
          ref="largeImageInputRef"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleLargeImageSelect"
        />
        <div v-if="largeImageUrl" class="image-preview">
          <img :src="largeImageUrl" alt="大图" />
          <el-button
            type="danger"
            size="small"
            circle
            class="remove-btn"
            @click="clearLargeImage"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <div v-else class="button-group">
          <el-button
            type="primary"
            size="small"
            @click="largeImageInputRef?.click()"
          >
            上传大图
          </el-button>
          <el-button
            type="success"
            size="small"
            :loading="screenshotLoading"
            :disabled="!currentDeviceId"
            @click="handleScreenshotClick"
          >
            截图
          </el-button>
        </div>
      </div>
    </div>

    <div class="debug-section">
      <div class="section-title">查询范围 (x,y,w,h)</div>
      <el-input
        v-model="regionInput"
        placeholder="例如: 0,0,100,100 (留空则查询全图)"
        size="small"
        clearable
      />
    </div>

    <div class="debug-section">
      <div class="section-title">偏色 (多个用|分割)</div>
      <el-input
        v-model="colorToleranceInput"
        placeholder="例如: C9C0B2-25211F|111111-222222"
        size="small"
        clearable
      />
    </div>

    <div class="debug-section">
      <el-button
        type="primary"
        size="small"
        :loading="matching"
        :disabled="!smallImageUrl || !largeImageUrl"
        @click="handleMatch"
        style="width: 100%"
      >
        {{ matching ? "匹配中..." : "开始匹配" }}
      </el-button>
    </div>

    <div class="debug-section result-section">
      <div class="section-title">匹配结果</div>
      <ImageDisplayArea
        :imageUrl="resultImageUrl"
        alt="匹配结果"
        placeholderText="匹配结果将显示在此处"
      />
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
import ImageDisplayArea from "./ImageDisplayArea.vue";

const props = defineProps({
  transparentImageUrl: {
    type: String,
    default: null,
  },
  currentDeviceId: {
    type: String,
    default: "",
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
  if ((!smallImageFile.value && !smallImageUrl.value) || (!largeImageFile.value && !largeImageUrl.value)) {
    ElMessage.warning("请先上传小图和大图");
    return;
  }

  matching.value = true;
  resultImageUrl.value = null;
  matchResult.value = null;

  try {
    // 读取文件为 base64
    let smallBase64;
    if (smallImageFile.value) {
      // 从文件读取
      smallBase64 = await fileToBase64(smallImageFile.value);
    } else if (smallImageUrl.value) {
      // 从 URL 中提取 base64（透明图的情况）
      const base64Data = smallImageUrl.value.split(",")[1];
      if (!base64Data) {
        ElMessage.error("无法从图片 URL 中提取 base64 数据");
        matching.value = false;
        return;
      }
      smallBase64 = base64Data;
    } else {
      ElMessage.warning("请先上传小图");
      matching.value = false;
      return;
    }
    
    // 读取大图为 base64
    let largeBase64;
    if (largeImageFile.value) {
      // 从文件读取
      largeBase64 = await fileToBase64(largeImageFile.value);
    } else if (largeImageUrl.value) {
      // 从 URL 中提取 base64（截图的情况）
      const base64Data = largeImageUrl.value.split(",")[1];
      if (!base64Data) {
        ElMessage.error("无法从图片 URL 中提取 base64 数据");
        matching.value = false;
        return;
      }
      largeBase64 = base64Data;
    } else {
      ElMessage.warning("请先上传大图");
      matching.value = false;
      return;
    }

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
      largeImage: largeBase64,
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
  gap: 10px;
  padding: 5px;
  max-height: 590px;
  overflow-y: auto;
}

.debug-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
}

.image-upload-area {
  min-height: 80px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  padding: 10px;
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

.image-preview img {
  max-width: 100%;
  max-height: 150px;
  object-fit: contain;
}

.remove-btn {
  position: absolute;
  top: 5px;
  right: 5px;
}

.result-section {
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.button-group {
  display: flex;
  gap: 5px;
  width: 100%;
}

.button-group .el-button {
  flex: 1;
}
</style>

