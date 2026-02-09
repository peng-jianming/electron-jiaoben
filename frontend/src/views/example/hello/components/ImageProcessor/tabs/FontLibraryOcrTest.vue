<template>
  <div class="font-library-ocr-test">
    <el-form size="small" label-width="72px" class="ocr-form">
      <el-form-item label="大图">
        <div class="image-upload-area">
          <input ref="largeImageInputRef" type="file" accept="image/*" class="hidden-input"
            @change="handleLargeImageSelect" />
          <div v-if="largeImageUrl" class="image-preview">
            <el-image :src="largeImageUrl" :preview-src-list="[largeImageUrl]" fit="contain" preview-teleported
              class="thumbnail-image" />
            <el-button type="danger" size="small" circle class="remove-btn" @click="clearLargeImage">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
          <div v-else class="upload-placeholder">
            <div class="upload-hint">不传则默认截图</div>
            <div class="button-group">
              <el-button type="primary" size="small" @click="largeImageInputRef?.click()">上传大图</el-button>
              <el-button type="success" size="small" :loading="screenshotLoading" :disabled="!currentDeviceId"
                @click="handleScreenshotClick">截图</el-button>
            </div>
          </div>
        </div>
      </el-form-item>
      <el-form-item label="范围">
        <el-input v-model="regionInput" placeholder="x,y,w,h（留空查全图）" size="small" clearable />
      </el-form-item>
      <el-form-item label="相似度">
        <div class="similarity-row">
          <el-slider v-model="similarity" :min="0.1" :max="1" :step="0.1" :format-tooltip="formatSimilarity"
            class="similarity-slider" />
          <span class="similarity-value">{{ similarity }}</span>
        </div>
      </el-form-item>
      <el-form-item label="文字间隔">
        <el-input v-model="charSpacingInput" placeholder="留空为无间隔；填数字如 5 表示水平/垂直间隔像素" size="small"
          clearable />
      </el-form-item>
    </el-form>

    <el-button type="primary" size="small" :loading="ocring"
      :disabled="!fontLibraryPath || (!largeImageUrl && !currentDeviceId)" @click="handleOcr" class="ocr-btn">
      {{ ocring ? "识别中..." : "开始识字" }}
    </el-button>

    <div class="result-section">
      <div class="result-label">识别结果：</div>
      <div class="result-text" :class="{ empty: !ocrResult && !ocring }">
        {{ ocrResult !== null ? ocrResult : (ocring ? "识别中..." : "结果将显示在此处") }}
      </div>
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

const props = defineProps({
  currentDeviceId: { type: String, default: "" },
  /** 字库路径：从字库 tab 选择字库后由父组件传入 */
  fontLibraryPath: { type: String, default: "" },
});

const largeImageInputRef = ref(null);
const largeImageUrl = ref(null);
const largeImageFile = ref(null);
const regionInput = ref("");
const similarity = ref(0.8);
const charSpacingInput = ref("");
const ocring = ref(false);
const ocrResult = ref(null);
const screenshotLoading = ref(false);
const isScreenshotPending = ref(false);
let ocrSocket = null;

const formatSimilarity = (val) => val.toFixed(1);

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

function clearLargeImage() {
  largeImageUrl.value = null;
  largeImageFile.value = null;
  if (largeImageInputRef.value) largeImageInputRef.value.value = "";
}

async function handleScreenshotClick() {
  if (!props.currentDeviceId) {
    ElMessage.warning("请先连接设备");
    return;
  }
  screenshotLoading.value = true;
  isScreenshotPending.value = true;
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "capture_screenshot",
      source: "font-library-ocr-test",
    });
    setTimeout(() => {
      if (isScreenshotPending.value) {
        isScreenshotPending.value = false;
        screenshotLoading.value = false;
        ElMessage.error("截图超时");
      }
    }, 10000);
  } catch (error) {
    console.error("截图失败:", error);
    ElMessage.error(`截图失败: ${error.message || "未知错误"}`);
    screenshotLoading.value = false;
    isScreenshotPending.value = false;
  }
}

function handleDeviceScreenshot(data) {
  screenshotLoading.value = false;
  isScreenshotPending.value = false;
  if (!data?.success || !data.image) {
    ElMessage.error(data?.error || "获取截图失败");
    return;
  }
  largeImageUrl.value = `data:image/png;base64,${data.image}`;
  largeImageFile.value = null;
  ElMessage.success("截图已设置为大图");
}

function initOcrSocket() {
  if (ocrSocket) return;
  ocrSocket = io("ws://localhost:7070");
  ocrSocket.on("connect", () => console.log("识字 Socket 连接成功"));
  ocrSocket.on("font-library-ocr-result", handleOcrResult);
  ocrSocket.on("device-screenshot", (data) => {
    if (isScreenshotPending.value) handleDeviceScreenshot(data);
  });
}

function handleOcrResult(data) {
  ocring.value = false;
  if (!data) {
    ElMessage.error("未收到识别结果");
    return;
  }
  if (!data.success) {
    ElMessage.error(data.error || "识字失败");
    ocrResult.value = "";
    return;
  }
  ocrResult.value = data.text != null ? String(data.text) : "";
  ElMessage.success("识字完成");
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target.result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function handleOcr() {
  if (!props.fontLibraryPath?.trim()) {
    ElMessage.warning("请先在字库标签页选择字库文件");
    return;
  }
  if (!largeImageFile.value && !largeImageUrl.value && !props.currentDeviceId) {
    ElMessage.warning("请先上传大图或连接设备以自动截图");
    return;
  }

  let largeBase64 = null;
  if (largeImageFile.value) {
    largeBase64 = await fileToBase64(largeImageFile.value);
  } else if (largeImageUrl.value) {
    const base64Data = largeImageUrl.value.split(",")[1];
    if (base64Data) largeBase64 = base64Data;
  }

  let region = null;
  if (regionInput.value.trim()) {
    const parts = regionInput.value.split(",").map((s) => s.trim());
    if (parts.length === 4) {
      const x = parseInt(parts[0], 10);
      const y = parseInt(parts[1], 10);
      const w = parseInt(parts[2], 10);
      const h = parseInt(parts[3], 10);
      if (!Number.isNaN(x) && !Number.isNaN(y) && !Number.isNaN(w) && !Number.isNaN(h)) {
        region = { x, y, w, h };
      }
    }
    if (!region) ElMessage.warning("区域格式错误，将查询全图");
  }

  let charSpacing = null;
  const raw = charSpacingInput.value.trim();
  if (raw) {
    const num = parseInt(raw, 10);
    if (!Number.isNaN(num) && num >= 0) charSpacing = num;
  }

  ocring.value = true;
  ocrResult.value = null;
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "font_library_ocr",
      fontLibraryPath: props.fontLibraryPath.trim(),
      largeImage: largeBase64,
      region,
      similarity: similarity.value,
      charSpacing,
    });
    setTimeout(() => {
      if (ocring.value) {
        ocring.value = false;
        ElMessage.error("识字超时");
      }
    }, 30000);
  } catch (error) {
    console.error("识字请求失败:", error);
    ElMessage.error(`识字失败: ${error.message || "未知错误"}`);
    ocring.value = false;
  }
}

onMounted(() => initOcrSocket());
onUnmounted(() => {
  if (ocrSocket) {
    ocrSocket.disconnect();
    ocrSocket = null;
  }
});
</script>

<style scoped>
.font-library-ocr-test {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
}

.ocr-form {
  flex-shrink: 0;
}

.ocr-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

.ocr-form :deep(.el-form-item__label) {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.hidden-input {
  display: none;
}

.image-upload-area {
  height: 72px;
  width: 100%;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.image-upload-area:hover {
  border-color: #94a3b8;
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
  height: 60px;
  object-fit: contain;
}

.remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.upload-hint {
  color: #94a3b8;
  font-size: 11px;
}

.button-group {
  display: flex;
  gap: 6px;
  width: 100%;
}

.button-group .el-button {
  flex: 1;
}

.similarity-row {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.similarity-slider {
  flex: 1;
}

.similarity-value {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  min-width: 28px;
  text-align: center;
}

.ocr-btn {
  width: 100%;
  margin-bottom: 6px;
  flex-shrink: 0;
}

.result-section {
  flex: 1;
  min-height: 60px;
  padding: 8px;
  border-radius: 8px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-label {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.result-text {
  font-size: 14px;
  color: #0f172a;
  word-break: break-all;
  white-space: pre-wrap;
  flex: 1;
}

.result-text.empty {
  color: #94a3b8;
  font-size: 12px;
}
</style>
