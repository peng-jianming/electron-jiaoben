<template>
    <div class="image-match-debug">
      <el-form size="small" label-width="52px" class="match-form">
        <el-form-item label="字库名">
          <el-autocomplete
            v-model="fontLibraryName"
            :fetch-suggestions="queryFontLibraryNames"
            placeholder="请输入字库名"
            size="small"
            clearable
            @select="handleFontLibraryNameSelect"
            class="full-width"
          />
        </el-form-item>
        <el-form-item label="大图">
          <div class="image-upload-area">
            <input ref="largeImageInputRef" type="file" accept="image/*" class="hidden-input"
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
            <div v-else class="upload-placeholder">
              <div class="upload-hint">不传则默认截图</div>
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
          <el-input v-model="regionInput" placeholder="x,y,w,h（留空查全图）" size="small" clearable />
        </el-form-item>
        <el-form-item label="相似度">
          <div class="similarity-row">
            <el-slider v-model="similarity" :min="0.1" :max="1" :step="0.1" :format-tooltip="formatSimilarity"
              class="similarity-slider" />
            <span class="similarity-value">{{ similarity }}</span>
          </div>
        </el-form-item>
      </el-form>
  
      <el-button type="primary" size="small" :loading="matching"
        :disabled="!fontLibraryName || (!largeImageUrl && !currentDeviceId)" @click="handleMatch"
        class="match-btn">
        {{ matching ? "匹配中..." : "开始匹配" }}
      </el-button>
  
      <div class="result-section">
        <el-image :src="resultImageUrl" :preview-src-list="[resultImageUrl]" fit="contain" preview-teleported
          class="result-image">
          <template #placeholder>
            <div class="result-placeholder">匹配结果将显示在此处</div>
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
  
  const props = defineProps({
    currentDeviceId: {
      type: String,
      default: "",
    },
    // 从右侧“偏色计算”标签页传入的已选偏色列表
    fontLibraryList: {
      type: Array,
      default: () => [],
    },
  });
  
  const largeImageInputRef = ref(null);
  const largeImageUrl = ref(null);
  const largeImageFile = ref(null);
  const regionInput = ref("");
  const fontLibraryName = ref("");
  const similarity = ref(0.8);
  const matching = ref(false);
  const resultImageUrl = ref(null);
  const matchResult = ref(null);
  const screenshotLoading = ref(false);
  const isScreenshotPending = ref(false);
  let matchSocket = null;
  
  // 格式化相似度显示
  const formatSimilarity = (val) => {
    return val.toFixed(1);
  };
  
  // 获取字库列表（从 props）
  const getFontLibraryList = () => {
    return props.fontLibraryList || [];
  };
  
  // 查询字库名（用于自动完成）
  const queryFontLibraryNames = (queryString, cb) => {
    const fontLibraryList = getFontLibraryList();
    // 获取所有唯一的字库名
    const uniqueNames = [...new Set(fontLibraryList.map(item => item.name).filter(Boolean))];
    // 过滤匹配的字库名
    const results = uniqueNames
      .filter(name => name.toLowerCase().includes(queryString.toLowerCase()))
      .map(name => ({ value: name }));
    cb(results);
  };
  
  // 处理字库名选择
  const handleFontLibraryNameSelect = (item) => {
    fontLibraryName.value = item.value;
  };
  
  // 初始化 Socket 连接
  function initMatchSocket() {
    if (matchSocket) {
      return;
    }
  
    matchSocket = io("ws://localhost:7070");
  
    matchSocket.on("connect", () => {
      console.log("匹配 Socket 连接成功");
    });
  
    matchSocket.on("font-library-match-result", (data) => {
      console.log("收到字库匹配结果:", data);
      handleMatchResult(data);
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
  
  // 清空大图
  function clearLargeImage() {
    largeImageUrl.value = null;
    largeImageFile.value = null;
    if (largeImageInputRef.value) {
      largeImageInputRef.value.value = "";
    }
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
    // 检查字库名
    if (!fontLibraryName.value || !fontLibraryName.value.trim()) {
      ElMessage.warning("请输入字库名");
      return;
    }
  
    // 检查是否有大图或设备ID（用于自动截图）
    if (!largeImageFile.value && !largeImageUrl.value && !props.currentDeviceId) {
      ElMessage.warning("请先上传大图或连接设备以自动截图");
      return;
    }
  
    // 获取字库列表
    const fontLibraryList = getFontLibraryList();
    if (!fontLibraryList || fontLibraryList.length === 0) {
      ElMessage.warning("字库列表为空，请先在字库制作标签页中加载字库");
      return;
    }
  
    // 根据字库名匹配所有符合字库名的信息组合成数组
    const matchedFontLibraries = fontLibraryList.filter(item => item.name === fontLibraryName.value);
    if (matchedFontLibraries.length === 0) {
      ElMessage.warning(`未找到字库名为"${fontLibraryName.value}"的字库`);
      return;
    }
  
    // 构建字库信息数组（格式：点阵&长,宽,点阵总数量&偏色&命名&偏移点击区域）
    const fontLibraryInfoArray = matchedFontLibraries.map(item => {
      return `${item.matrix}&${item.width},${item.height},${item.totalCount}&${item.deviation}&${item.name}&${item.clickOffsetArea}`;
    });
  
    matching.value = true;
    resultImageUrl.value = null;
    matchResult.value = null;
  
    try {
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
  
      // 发送字库匹配请求
      await ipc.invoke(ipcApiRoute.sendToPython, {
        type: "font_library_match",
        fontLibraryInfoArray: fontLibraryInfoArray,
        largeImage: largeBase64, // 如果为 null，后端会自动截图
        region: region,
        similarity: similarity.value,
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
    height: 100%;
    overflow-y: auto;
  }
  
  .match-form {
    flex-shrink: 0;
  }

  .match-form :deep(.el-form-item) {
    margin-bottom: 8px;
  }

  .match-form :deep(.el-form-item__label) {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
  }

  .full-width {
    width: 100%;
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
    transition: border-color 0.2s;
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

  .match-btn {
    width: 100%;
    margin-bottom: 6px;
    flex-shrink: 0;
  }
  
  .result-section {
    flex: 1;
    min-height: 80px;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 8px;
    background: #0f172a;
    background-image:
      linear-gradient(45deg, #1e293b 25%, transparent 25%),
      linear-gradient(-45deg, #1e293b 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #1e293b 75%),
      linear-gradient(-45deg, transparent 75%, #1e293b 75%);
    background-size: 12px 12px;
    background-position: 0 0, 0 6px, 6px -6px, -6px 0px;
    color: #64748b;
    font-size: 12px;
  }

  .result-image {
    height: 100%;
    width: 100%;
  }

  .result-placeholder {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
    color: #475569;
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
  </style>
  