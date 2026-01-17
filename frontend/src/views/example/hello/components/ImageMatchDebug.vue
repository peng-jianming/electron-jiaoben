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
        <el-button
          v-else
          type="primary"
          size="small"
          @click="smallImageInputRef?.click()"
        >
          上传小图
        </el-button>
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
        <el-button
          v-else
          type="primary"
          size="small"
          @click="largeImageInputRef?.click()"
        >
          上传大图
        </el-button>
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
      <div v-if="resultImageUrl" class="result-image-container">
        <img :src="resultImageUrl" alt="匹配结果" />
        <div v-if="matchResult" class="result-info">
          <div>位置: ({{ matchResult.x }}, {{ matchResult.y }})</div>
          <div>尺寸: {{ matchResult.w }} × {{ matchResult.h }}</div>
          <div>相似度: {{ (matchResult.similarity * 100).toFixed(2) }}%</div>
        </div>
      </div>
      <div v-else class="result-placeholder">
        匹配结果将显示在此处
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

// 处理匹配
async function handleMatch() {
  if (!smallImageFile.value || !largeImageFile.value) {
    ElMessage.warning("请先上传小图和大图");
    return;
  }

  matching.value = true;
  resultImageUrl.value = null;
  matchResult.value = null;

  try {
    // 读取文件为 base64
    const smallBase64 = await fileToBase64(smallImageFile.value);
    const largeBase64 = await fileToBase64(largeImageFile.value);

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
}

.result-image-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow: auto;
}

.result-image-container img {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
}

.result-info {
  font-size: 12px;
  color: #606266;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.result-placeholder {
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  padding: 20px;
  text-align: center;
  color: #909399;
  font-size: 12px;
}
</style>

