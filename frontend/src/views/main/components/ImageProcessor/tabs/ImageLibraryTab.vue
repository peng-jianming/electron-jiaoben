<template>
  <div class="image-library-container">
    <!-- 图片库文件选择 -->
    <el-input
      v-model="npzPath"
      placeholder="请选择图片库 .npz 文件"
      readonly
      class="file-input"
      size="small"
    >
      <template #prepend>
        <el-button @click="handleSelectNpz" :loading="fileLoading">选择图片库</el-button>
      </template>
    </el-input>

    <!-- 图片列表 -->
    <el-table
      :data="filteredImageList"
      height="100%"
      size="small"
      empty-text="请先选择图片库 .npz 文件"
      class="image-table"
      :header-cell-style="{
        background: '#f8fafc',
        color: '#64748b',
        fontSize: '11px',
        fontWeight: 600,
        borderBottom: '1px solid #e2e8f0'
      }"
      :cell-style="{ fontSize: '12px', padding: '4px 0' }"
    >
      <el-table-column type="index" label="#" width="36" />

      <el-table-column label="预览" width="72">
        <template #default="scope">
          <div class="thumb-cell">
            <el-image
              v-if="scope.row.thumbUrl"
              :src="scope.row.thumbUrl"
              :preview-src-list="scope.row.fullUrl ? [scope.row.fullUrl] : []"
              preview-teleported
              fit="contain"
              class="thumb-image"
            />
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="name" min-width="120">
        <template #header>
          <div class="name-header-with-filter">
            <span>名称</span>
            <el-input
              v-model="nameFilter"
              placeholder="筛选"
              size="small"
              clearable
              class="name-filter-input"
            />
          </div>
        </template>
        <template #default="scope">
          <div v-if="scope.row.editing" class="name-edit-cell">
            <el-input
              v-model="scope.row.name"
              size="small"
              @blur="handleNameBlur(scope.row)"
              @keyup.enter="handleNameBlur(scope.row)"
              :ref="(el) => { if (el) scope.row.inputRef = el; }"
            />
          </div>
          <div
            v-else
            class="name-cell"
            :title="scope.row.name"
            @click="handleNameClick(scope.row)"
          >
            {{ scope.row.name || "-" }}
          </div>
        </template>
      </el-table-column>

      <!-- <el-table-column label="尺寸" width="110">
        <template #default="scope">
          <span class="size-cell">
            {{ scope.row.width }} × {{ scope.row.height }}
            <span v-if="scope.row.channels"> ({{ scope.row.channels }})</span>
          </span>
        </template>
      </el-table-column> -->

      <el-table-column label="操作" width="200">
        <template #header>
          <div class="action-header">
            <span>操作</span>
            <el-button type="primary" size="small" link @click="handleOpenAddDrawer">
              新增
            </el-button>
          </div>
        </template>
        <template #default="scope">
          <el-button type="primary" size="small" link @click.stop="handleTest(scope.row)">
            测试
          </el-button>
          <el-button type="danger" size="small" link @click.stop="handleDelete(scope.row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 模板匹配测试弹窗 -->
    <el-dialog
      v-model="testDialogVisible"
      :title="testDialogTitle"
      width="600px"
      destroy-on-close
      :close-on-click-modal="false"
      append-to-body
    >
      <div class="test-dialog-body">
        <el-form size="small" label-width="60px">
          <el-form-item label="小图">
            <div class="template-info">
              <span class="template-name">{{ currentTestRow?.name || '-' }}</span>
              <span class="template-size">
                {{ currentTestRow?.width }} × {{ currentTestRow?.height }}
              </span>
            </div>
          </el-form-item>
          <el-form-item label="大图">
            <div class="image-upload-area">
              <input
                ref="largeImageInputRef"
                type="file"
                accept="image/*"
                class="hidden-input"
                @change="handleLargeImageSelect"
              />
              <div v-if="largeImageUrl" class="image-preview">
                <el-image
                  :src="largeImageUrl"
                  :preview-src-list="[largeImageUrl]"
                  fit="contain"
                  class="thumbnail-image"
                  preview-teleported
                />
                <el-button
                  type="danger"
                  size="small"
                  circle
                  class="remove-btn"
                  @click="clearLargeImage"
                >
                  清
                </el-button>
              </div>
              <div v-else class="upload-placeholder">
                <div class="upload-hint">不传则默认截图</div>
                <div class="button-group">
                  <el-button type="primary" size="small" @click="largeImageInputRef?.click()">
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
          </el-form-item>
          <el-form-item label="范围">
            <el-input
              v-model="regionInput"
              placeholder="x,y,w,h（留空查全图）"
              size="small"
              clearable
            />
          </el-form-item>
          <el-form-item label="相似度">
            <div class="similarity-row">
              <el-slider
                v-model="similarity"
                :min="0.1"
                :max="1"
                :step="0.1"
              />
              <span class="similarity-value">{{ similarity.toFixed(1) }}</span>
            </div>
          </el-form-item>
        </el-form>

        <el-button
          type="primary"
          size="small"
          :loading="matching"
          :disabled="!currentTemplateBase64"
          @click="handleMatch"
          class="match-btn"
        >
          {{ matching ? "匹配中..." : "开始匹配" }}
        </el-button>

        <div class="result-section">
          <div class="result-cell">
            <div class="result-label">{{ processedResultCaption }}</div>
            <el-image
              :src="processedImageUrl"
              :preview-src-list="processedPreviewList"
              fit="contain"
              class="result-image"
              preview-teleported
            >
              <template #placeholder>
                <div class="preview-placeholder">匹配开始后显示与算法一致的搜索区</div>
              </template>
            </el-image>
          </div>
          <div class="result-cell">
            <div class="result-label">匹配标注（命中阈值时在原图上画框）</div>
            <el-image
              :src="resultImageUrl"
              :preview-src-list="resultPreviewList"
              fit="contain"
              class="result-image"
              preview-teleported
            >
              <template #placeholder>
                <div class="preview-placeholder">达到相似度阈值后显示标注图</div>
              </template>
            </el-image>
          </div>
        </div>
      </div>
    </el-dialog>

    <ImageSelectionDrawer
      ref="imageSelectionDrawerRef"
      v-model="addDrawerVisible"
      :current-image="currentImage"
      :selection-rect="selectionRect"
      :require-name="true"
      title="新增图片资源"
      subtitle="基于当前圈选图片新增图片资源，并按命名保存"
      selection-type="imageLibraryClickOffsetArea"
      :on-confirm="handleConfirmAddByDrawer"
      @start-code-generator-selection="(type) => emit('start-code-generator-selection', type)"
      @stop-code-generator-selection="emit('stop-code-generator-selection')"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { io } from "socket.io-client";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import ImageSelectionDrawer from "./ImageSelectionDrawer.vue";

const props = defineProps({
  currentDeviceId: {
    type: String,
    default: "",
  },
  currentImage: {
    type: Object,
    default: null,
  },
  selectionRect: {
    type: Object,
    default: null,
  },
});
const emit = defineEmits(["start-code-generator-selection", "stop-code-generator-selection"]);

const npzPath = ref("");
const fileLoading = ref(false);
const imageList = ref([]);
const nameFilter = ref("");
let imageSocket = null;
const isSyncingFromFile = ref(false);
let syncTimer = null;
/** 初始化时是否已从 DB 加载过路径（仅 socket 连接成功后加载一次，避免未连上就请求导致超时） */
let initialLoadFromDBDone = false;
/** loadImageLibrary 的 15s 超时定时器 id，用于在收到结果或卸载时清除 */
let loadLibraryTimeoutId = null;
/** 模板匹配请求：避免多次点击叠加多个 setTimeout 导致误报超时或 matching 无法复位 */
let imageMatchRequestTimeoutId = null;

// 测试相关状态
const testDialogVisible = ref(false);
const addDrawerVisible = ref(false);
const imageSelectionDrawerRef = ref(null);
const currentTestRow = ref(null);
const largeImageInputRef = ref(null);
const largeImageUrl = ref(null);
const largeImageFile = ref(null);
const regionInput = ref("");
const similarity = ref(0.8);
/** gray：灰度相关匹配；color：BGR 三通道平方差（配置项「彩图」测试时传入） */
const matchMode = ref("gray");
const matching = ref(false);

const testDialogTitle = computed(() =>
  matchMode.value === "color" ? "模板匹配测试（彩图 · 平方差）" : "模板匹配测试"
);
const processedResultCaption = computed(() =>
  matchMode.value === "color"
    ? "处理后（搜索区彩图，与匹配一致）"
    : "处理后（搜索区灰度，与匹配一致）"
);
const resultImageUrl = ref(null);
const processedImageUrl = ref(null);
const processedPreviewList = computed(() =>
  processedImageUrl.value ? [processedImageUrl.value] : []
);
const resultPreviewList = computed(() =>
  resultImageUrl.value ? [resultImageUrl.value] : []
);
const screenshotLoading = ref(false);
const isScreenshotPending = ref(false);
const currentTemplateBase64 = ref("");
const currentTemplateCandidates = ref([]);
const filteredImageList = computed(() => {
  const keyword = (nameFilter.value || "").trim().toLowerCase();
  if (!keyword) return imageList.value;
  return imageList.value.filter((row) =>
    (row.name || "").toLowerCase().includes(keyword)
  );
});

function initImageSocket() {
  if (imageSocket) {
    return;
  }

  imageSocket = io("ws://localhost:7070");

  imageSocket.on("connect", () => {
    console.log("图片库 Socket 连接成功");
    // 仅在首次连接成功后从 DB 加载配置并加载图片库，避免在 socket 未连上时发请求导致结果收不到而超时
    if (!initialLoadFromDBDone) {
      initialLoadFromDBDone = true;
      loadImageLibraryPathFromDB();
    }
  });

  imageSocket.on("image-library", (data) => {
    const items = data?.items;
    console.log("收到图片库结果:", {
      success: data?.success,
      error: data?.error,
      itemCount: Array.isArray(items) ? items.length : 0,
    });
    handleImageLibraryResult(data);
  });

  imageSocket.on("image-match-result", (data) => {
    console.log("收到图片库模板匹配结果:", {
      success: data?.success,
      error: data?.error,
      hasResultImage: !!data?.resultImage,
      hasProcessedImage: !!data?.processedImage,
    });
    handleMatchResult(data);
  });

  imageSocket.on("device-screenshot", (data) => {
    console.log("收到设备截图 (ImageLibraryTab):", {
      success: data?.success,
      source: data?.source,
      pending: isScreenshotPending.value,
      imageBase64Chars: typeof data?.image === "string" ? data.image.length : 0,
    });
    if (isScreenshotPending.value) {
      handleDeviceScreenshot(data);
    }
  });
}

async function handleSelectNpz() {
  fileLoading.value = true;
  try {
    const dialogResult = await ipc.invoke(ipcApiRoute.openFileDialog, {
      title: "选择图片库 .npz 文件",
      defaultPath: npzPath.value || "",
      filters: [
        { name: "Numpy 图片库文件", extensions: ["npz"] },
        { name: "所有文件", extensions: ["*"] },
      ],
    });

    if (
      !dialogResult ||
      !dialogResult.success ||
      dialogResult.canceled ||
      !dialogResult.filePath
    ) {
      fileLoading.value = false;
      return;
    }

    isSyncingFromFile.value = true;
    npzPath.value = dialogResult.filePath;
    imageList.value = [];

    await loadImageLibrary();
    await saveImageLibraryPathToDB();
  } catch (error) {
    console.error("选择图片库失败:", error);
    ElMessage.error("选择图片库失败: " + (error.message || "未知错误"));
    isSyncingFromFile.value = false;
  } finally {
    fileLoading.value = false;
  }
}

// 保存图片库路径到本地配置（与 ConfigTab/example 一致）
async function saveImageLibraryPathToDB() {
  try {
    await ipc.invoke(ipcApiRoute.savePaths, {
      imageLibraryPath: npzPath.value || "",
    });
  } catch (error) {
    console.error("保存图片库路径失败:", error);
  }
}

// 从本地配置加载图片库路径并在页面启动时自动加载
async function loadImageLibraryPathFromDB() {
  try {
    const result = await ipc.invoke(ipcApiRoute.getPaths);
    if (result && result.success && result.data && result.data.imageLibraryPath) {
      isSyncingFromFile.value = true;
      npzPath.value = result.data.imageLibraryPath;
      await loadImageLibrary();
      // 若加载超时或失败，handleImageLibraryResult 会设回 false；若一直没收到结果，这里兜底解除
      setTimeout(() => {
        isSyncingFromFile.value = false;
      }, 2000);
    }
  } catch (error) {
    console.error("加载图片库路径失败:", error);
    isSyncingFromFile.value = false;
  }
}

async function loadImageLibrary() {
  if (!npzPath.value) {
    ElMessage.warning("请先选择图片库 .npz 文件");
    return;
  }

  try {
    if (loadLibraryTimeoutId) {
      clearTimeout(loadLibraryTimeoutId);
      loadLibraryTimeoutId = null;
    }
    fileLoading.value = true;
    // 发送请求到 Python，实际数据通过 Socket 返回
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "load_image_library",
      npzPath: npzPath.value,
    });

    // 设置一个简单的超时提示，收到结果时会在 handleImageLibraryResult 里清除
    loadLibraryTimeoutId = setTimeout(() => {
      loadLibraryTimeoutId = null;
      if (fileLoading.value && imageList.value.length === 0) {
        fileLoading.value = false;
        ElMessage.error("加载图片库超时");
      }
    }, 15000);
  } catch (error) {
    console.error("加载图片库请求失败:", error);
    ElMessage.error("加载图片库请求失败: " + (error.message || "未知错误"));
    if (loadLibraryTimeoutId) {
      clearTimeout(loadLibraryTimeoutId);
      loadLibraryTimeoutId = null;
    }
    fileLoading.value = false;
  }
}

function handleImageLibraryResult(data) {
  if (loadLibraryTimeoutId) {
    clearTimeout(loadLibraryTimeoutId);
    loadLibraryTimeoutId = null;
  }
  fileLoading.value = false;

  if (!data || !data.success) {
    // “图片库中没有有效的图片数据”不提示，仅静默清空
    const noValidDataMsg = "图片库中没有有效的图片数据";
    if (data?.error !== noValidDataMsg) {
      ElMessage.error(data?.error || "加载图片库失败");
    }
    imageList.value = [];
    if (syncTimer) { clearTimeout(syncTimer); syncTimer = null; }
    setTimeout(() => { isSyncingFromFile.value = false; }, 800);
    return;
  }

  isSyncingFromFile.value = true;

  const items = Array.isArray(data.items) ? data.items : [];
  if (!items.length) {
    imageList.value = [];
    if (syncTimer) { clearTimeout(syncTimer); syncTimer = null; }
    setTimeout(() => { isSyncingFromFile.value = false; }, 800);
    return;
  }

  imageList.value = items.map((item, index) => {
    const base = item.image ? `data:image/png;base64,${item.image}` : null;
    return {
      id: index,
      name: item.name || `图片${index + 1}`,
      originalName: null,
      editing: false,
      inputRef: null,
      width: item.width || 0,
      height: item.height || 0,
      channels: item.channels || 0,
      fullUrl: base,
      thumbUrl: base,
      rawBase64: item.image || "",
    };
  });

  // 初始化从配置加载时不提示，仅用户手动选择图片库时提示
  if (!isSyncingFromFile.value) {
    ElMessage.success(`已加载 ${imageList.value.length} 张图片`);
  }

  // 清除 watcher 可能已排队的旧同步任务，然后延迟超过防抖时间(500ms)再解除保护
  if (syncTimer) { clearTimeout(syncTimer); syncTimer = null; }
  setTimeout(() => {
    isSyncingFromFile.value = false;
  }, 800);
}

async function handleNameClick(row) {
  if (!row) return;
  if (!row.originalName) {
    row.originalName = row.name || "";
  }
  row.editing = true;
  await nextTick();
  if (row.inputRef) {
    const inputEl = row.inputRef.$el?.querySelector("input") || row.inputRef.$el || row.inputRef;
    if (inputEl) {
      inputEl.focus();
      if (inputEl.select) {
        inputEl.select();
      }
    }
  }
}

function hasDuplicateName(targetRow, name) {
  const normalized = String(name || "").trim();
  return imageList.value.some(
    (row) => row !== targetRow && String(row?.name || "").trim() === normalized
  );
}

function handleNameBlur(row) {
  if (!row) return;
  row.editing = false;
  const oldName = String(row.originalName || row.name || "").trim();
  const newName = String(row.name || "").trim();

  if (!newName) {
    row.name = oldName;
    row.originalName = null;
    ElMessage.warning("名称不能为空");
    return;
  }
  if (newName === oldName) {
    row.name = newName;
    row.originalName = null;
    return;
  }
  if (hasDuplicateName(row, newName)) {
    row.name = oldName;
    row.originalName = null;
    ElMessage.error("存在命名相同，不允许修改");
    return;
  }

  row.name = newName;
  row.originalName = null;
  ElMessage.success("名称已修改");
}

async function handleDelete(row) {
  if (!row) return;
  const name = row.name || "该图片";
  try {
    await ElMessageBox.confirm(`确定要删除「${name}」吗？删除后将从图片库中移除并同步到 .npz 文件。`, "删除确认", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
  } catch {
    return;
  }
  const index = imageList.value.findIndex((item) => item === row || (item.id !== undefined && item.id === row.id));
  if (index !== -1) {
    imageList.value.splice(index, 1);
    ElMessage.success("已删除");
    // watcher 不会自动同步空列表，所以删除最后一项时需要显式同步
    if (imageList.value.length === 0) {
      syncImageLibraryToNpz();
    }
  }
}

function handleTest(row) {
  if (!row || !row.fullUrl) {
    ElMessage.warning("请先选择要测试的图片模板");
    return;
  }
  openTestWithRow(row, {});
}

/** 按图片名打开测试弹框（供配置页“测试”使用：名称与 testFontLibraryName 一致的那张图传到后端测试） */
function openTestByImageName(name, options = {}) {
  const trimmedName = (name || "").trim();
  if (!trimmedName) {
    ElMessage.warning("图片名不能为空");
    return false;
  }
  const escaped = trimmedName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  // 支持：
  // - 基础名
  // - 基础名_数字
  // - 基础名_数字_偏移坐标（新规则）
  // - 基础名_偏移坐标（历史兼容）
  const pattern = new RegExp(
    `^${escaped}(?:_\\d+)?(?:_-?\\d+,-?\\d+,\\d+,\\d+)?$`
  );
  const matchedRows = imageList.value.filter((item) =>
    pattern.test((item.name || "").trim())
  );
  if (!matchedRows.length) {
    ElMessage.warning(
      `图片库中未找到名为「${trimmedName}」前缀（含序号/偏移坐标后缀）的图片`
    );
    return false;
  }
  openTestWithRows(matchedRows, options);
  return true;
}

function openTestWithRow(row, options = {}) {
  openTestWithRows([row], options);
}

function openTestWithRows(rows, options = {}) {
  const validRows = (rows || []).filter((row) => row && row.fullUrl);
  if (!validRows.length) {
    ElMessage.error("当前模板图片数据无效，无法测试");
    return;
  }
  currentTemplateCandidates.value = validRows;
  const firstRow = validRows[0];
  currentTestRow.value = firstRow;
  // 记录模板 base64（去掉 data URL 前缀）
  if (firstRow.rawBase64) {
    currentTemplateBase64.value = firstRow.rawBase64;
  } else if (firstRow.fullUrl && firstRow.fullUrl.includes(",")) {
    currentTemplateBase64.value = firstRow.fullUrl.split(",")[1] || "";
  } else {
    currentTemplateBase64.value = "";
  }
  if (!currentTemplateBase64.value) {
    ElMessage.error("当前模板图片数据无效，无法测试");
    return;
  }
  // 重置测试状态
  largeImageUrl.value = null;
  largeImageFile.value = null;
  regionInput.value = options.region != null ? String(options.region).trim() : "";
  similarity.value =
    options.similarity != null && !Number.isNaN(Number(options.similarity))
      ? Number(options.similarity)
      : 0.8;
  matchMode.value = options.matchMode === "color" ? "color" : "gray";
  resultImageUrl.value = null;
  processedImageUrl.value = null;
  matching.value = false;
  testDialogVisible.value = true;
}

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
  if (largeImageInputRef.value) {
    largeImageInputRef.value.value = "";
  }
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
      source: "image-library-test",
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

  if (!data || !data.success || !data.image) {
    ElMessage.error(data?.error || "获取截图失败");
    return;
  }

  const url = `data:image/png;base64,${data.image}`;
  largeImageUrl.value = url;
  largeImageFile.value = null;
  ElMessage.success("截图已设置为大图");
}

async function handleMatch() {
  if (!currentTemplateCandidates.value.length) {
    ElMessage.warning("当前模板图片数据无效");
    return;
  }

  if (!largeImageFile.value && !largeImageUrl.value && !props.currentDeviceId) {
    ElMessage.warning("请先上传大图或连接设备以自动截图");
    return;
  }

  matching.value = true;
  resultImageUrl.value = null;
  processedImageUrl.value = null;

  if (imageMatchRequestTimeoutId != null) {
    clearTimeout(imageMatchRequestTimeoutId);
    imageMatchRequestTimeoutId = null;
  }

  try {
    let largeBase64 = null;
    if (largeImageFile.value) {
      largeBase64 = await fileToBase64(largeImageFile.value);
    } else if (largeImageUrl.value && largeImageUrl.value.includes(",")) {
      largeBase64 = largeImageUrl.value.split(",")[1] || null;
    }

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
        ElMessage.warning("范围格式错误，将匹配全图");
      }
    }

    const templateImages = currentTemplateCandidates.value
      .map((item) => {
        const itemBase64 =
          item.rawBase64 ||
          (item.fullUrl && item.fullUrl.includes(",") ? item.fullUrl.split(",")[1] : "");
        if (!itemBase64) return null;
        return { name: item.name || "", image: itemBase64 };
      })
      .filter(Boolean);

    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "image_library_match",
      templateImages,
      largeImage: largeBase64,
      region,
      similarity: similarity.value,
      matchMode: matchMode.value,
    });

    imageMatchRequestTimeoutId = setTimeout(() => {
      imageMatchRequestTimeoutId = null;
      if (matching.value) {
        matching.value = false;
        ElMessage.error("匹配超时");
      }
    }, 30000);
  } catch (error) {
    console.error("匹配失败:", error);
    ElMessage.error(`匹配失败: ${error.message || "未知错误"}`);
    if (imageMatchRequestTimeoutId != null) {
      clearTimeout(imageMatchRequestTimeoutId);
      imageMatchRequestTimeoutId = null;
    }
    matching.value = false;
  }
}

function handleMatchResult(data) {
  if (imageMatchRequestTimeoutId != null) {
    clearTimeout(imageMatchRequestTimeoutId);
    imageMatchRequestTimeoutId = null;
  }
  const wasOurRequest = matching.value;
  matching.value = false;

  if (data?.processedImage) {
    processedImageUrl.value = `data:image/png;base64,${data.processedImage}`;
  } else {
    processedImageUrl.value = null;
  }

  if (!data || !data.success) {
    resultImageUrl.value = null;
    if (wasOurRequest) {
      ElMessage.error(data?.error || "匹配失败");
    }
    return;
  }

  if (data.resultImage) {
    resultImageUrl.value = `data:image/png;base64,${data.resultImage}`;
  } else {
    resultImageUrl.value = null;
  }

  if (wasOurRequest) {
    if (data.result) {
      ElMessage.success("匹配完成");
    } else {
      ElMessage.warning("未找到匹配位置");
    }
  }
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

onMounted(() => {
  initImageSocket();
  // 不再在此处调用 loadImageLibraryPathFromDB，改为在 socket "connect" 后再调用，避免未连上就请求导致收不到结果而超时
});

onUnmounted(() => {
  if (loadLibraryTimeoutId) {
    clearTimeout(loadLibraryTimeoutId);
    loadLibraryTimeoutId = null;
  }
  if (imageMatchRequestTimeoutId != null) {
    clearTimeout(imageMatchRequestTimeoutId);
    imageMatchRequestTimeoutId = null;
  }
  if (imageSocket) {
    imageSocket.disconnect();
    imageSocket = null;
  }
});

// 将当前表格数据同步到 .npz 图片库（公共函数，供 watch 和外部显式调用）
async function syncImageLibraryToNpz(val) {
  if (!npzPath.value) return;
  if (isSyncingFromFile.value) return;
  if (imageList.value.some((row) => row && row.editing)) return;

  const source = val || imageList.value;
  try {
    const items = (source || []).map((row, index) => ({
      name: row.name || `图片${index + 1}`,
      image:
        row.rawBase64 ||
        (row.fullUrl && row.fullUrl.includes(",") ? row.fullUrl.split(",")[1] : ""),
    })).filter((item) => item.image);

    // 列表非空但所有图片数据无效 → 数据异常，中止保存防止清空 npz
    if (items.length === 0 && (source || []).length > 0) {
      console.error("同步到 npz 被中止：列表不为空但所有图片数据无效");
      ElMessage.error("同步失败：图片数据无效，已中止保存以防止数据丢失");
      return;
    }

    // 检查同名：存在同名时直接阻止保存
    const nameCount = {};
    items.forEach((item) => {
      const n = (item.name || "").trim();
      nameCount[n] = (nameCount[n] || 0) + 1;
    });
    const duplicateNames = Object.keys(nameCount).filter((n) => nameCount[n] > 1);
    if (duplicateNames.length > 0) {
      ElMessage.error(`存在命名相同（${duplicateNames.join("、")}），不允许保存`);
      return;
    }

    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "save_image_library",
      npzPath: npzPath.value,
      items,
    });
  } catch (error) {
    console.error("同步图片库到 .npz 失败:", error);
    ElMessage.error("同步图片库到 .npz 失败: " + (error.message || "未知错误"));
  }
}

// 监听表格数据变化，同步到 .npz 图片库（以当前表格为唯一来源）
watch(
  imageList,
  (val) => {
    if (!npzPath.value) return;
    if (isSyncingFromFile.value) return;
    if (imageList.value.some((row) => row && row.editing)) return;
    // 空列表不自动同步，防止竞态条件清空 npz（显式删除最后一项会单独处理）
    if (!val || val.length === 0) return;

    if (syncTimer) {
      clearTimeout(syncTimer);
    }

    // 简单防抖，避免频繁写盘
    syncTimer = setTimeout(() => {
      syncImageLibraryToNpz(val);
    }, 500);
  },
  { deep: true }
);

/**
 * 判断资源名是否与待删除名匹配：
 * - 统一按“配置名前缀族”删除：精确匹配 或 以 `${nameToDelete}_` 开头
 * - 例如：删除 `a_b` 时，同时删除 `a_b`、`a_b_1`、`a_b_2`
 */
function nameMatchesDeletion(itemName, nameToDelete) {
  const n = (itemName || "").trim();
  const t = nameToDelete.trim();
  return n === t || n.startsWith(t + "_");
}

/** 按名称删除图片库中与 name 相同的资源（供 ConfigTab 删除配置项后联动使用，不再弹确认） */
function deleteByName(name) {
  if (!name || typeof name !== "string") return false;
  const trimmed = name.trim();
  const indices = imageList.value
    .map((item, i) => (nameMatchesDeletion(item.name, trimmed) ? i : -1))
    .filter((i) => i >= 0)
    .sort((a, b) => b - a);
  if (indices.length === 0) return false;
  const removedUrls = new Set(indices.map((i) => imageList.value[i]?.fullUrl).filter(Boolean));
  indices.forEach((i) => imageList.value.splice(i, 1));
  return true;
}

/** 仅删除一条：配置页特征列表用，避免前缀族误删 */
function deleteById(id) {
  if (id == null) return false;
  const i = imageList.value.findIndex((item) => item.id === id);
  if (i < 0) return false;
  const removedUrl = imageList.value[i]?.fullUrl;
  imageList.value.splice(i, 1);
  return true;
}

/** 无 id 时按名称精确匹配删一条 */
function deleteByExactName(name) {
  if (!name || typeof name !== "string") return false;
  const t = name.trim();
  const i = imageList.value.findIndex((item) => (item.name || "").trim() === t);
  if (i < 0) return false;
  const removedUrl = imageList.value[i]?.fullUrl;
  imageList.value.splice(i, 1);
  return true;
}

const handleOpenAddDrawer = () => {
  if (!npzPath.value) {
    ElMessage.warning("请先选择图片库 .npz 文件");
    return;
  }
  if (!props.currentImage?.url) {
    ElMessage.warning("当前没有图片，无法新增");
    return;
  }
  imageSelectionDrawerRef.value?.resetForOpen?.({
    resetName: true,
  });
  addDrawerVisible.value = true;
};

const handleConfirmAddByDrawer = async (payload) => {
  const name = String(payload?.name || "").trim();
  const clickOffsetArea = payload?.clickOffsetArea || "0,0,0,0";
  const previewDataUrl = payload?.previewDataUrl || "";
  if (!name) {
    ElMessage.warning("请输入命名");
    return false;
  }
  if (!previewDataUrl) {
    ElMessage.warning("当前没有可添加图片");
    return false;
  }

  const base64 =
    previewDataUrl.indexOf(",") >= 0 ? previewDataUrl.split(",")[1] : previewDataUrl;
  if (!base64) {
    ElMessage.warning("图片数据无效，无法保存");
    return false;
  }

  let width = 0;
  let height = 0;
  if (props.selectionRect?.w > 0 && props.selectionRect?.h > 0) {
    width = props.selectionRect.w;
    height = props.selectionRect.h;
  }

  const added = await addImageItemFromConfig({
    name: `${name}_1_${clickOffsetArea}`,
    width,
    height,
    base64,
  });

  if (added) {
    ElMessage.success("图片添加成功");
    return true;
  }
  ElMessage.error("图片添加失败");
  return false;
};

const addImageItemFromConfig = async (payload) => {
  const { name, width, height, base64 } = payload || {};
  if (!base64) return false;
  const baseName = (name || `图片${imageList.value.length + 1}`).trim();
  const existingNames = new Set(
    imageList.value.map((item) => (item.name || "").trim())
  );
  let displayName = baseName;
  // 统一命名：若包含偏移坐标，使用「基础名_序号_坐标」，且序号在同一基础名下全局唯一
  const offsetWithSeqMatch = baseName.match(
    /^(.*?)(?:_(\d+))?_(-?\d+,-?\d+,\d+,\d+)$/
  );
  if (offsetWithSeqMatch) {
    const plainBase = (offsetWithSeqMatch[1] || "").trim();
    const offsetPart = offsetWithSeqMatch[3];
    const usedSeq = new Set();
    const seqReg = new RegExp(
      `^${plainBase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}_(\\d+)(?:_|$)`
    );
    existingNames.forEach((n) => {
      const m = String(n || "").match(seqReg);
      if (!m) return;
      const seq = Number(m[1]);
      if (Number.isFinite(seq) && seq > 0) usedSeq.add(seq);
    });
    let counter = Number(offsetWithSeqMatch[2] || 1);
    if (!Number.isFinite(counter) || counter < 1) counter = 1;
    while (usedSeq.has(counter)) {
      counter++;
    }
    displayName = `${plainBase}_${counter}_${offsetPart}`;
  } else if (existingNames.has(displayName)) {
    let counter = 1;
    while (existingNames.has(`${baseName}_${counter}`)) {
      counter++;
    }
    displayName = `${baseName}_${counter}`;
  }
  const fullUrl = `data:image/png;base64,${base64}`;
  const newItem = {
    id: Date.now() + Math.random(),
    name: displayName,
    originalName: null,
    editing: false,
    inputRef: null,
    width: width || 0,
    height: height || 0,
    channels: 3,
    fullUrl,
    thumbUrl: fullUrl,
    rawBase64: base64,
  };
  imageList.value.push(newItem);
  return true;
};

// 暴露给父组件的方法
defineExpose({
  /** 供配置页特征列表等订阅，保持与列表变更同步 */
  imageList,
  getNpzPath: () => npzPath.value || "",
  deleteByName,
  deleteById,
  deleteByExactName,
  /** 按图片名打开模板匹配测试弹框（名称与 testFontLibraryName 一致时由配置页调用） */
  openTestByImageName,
  // 从外部显式触发一次同步（例如 ConfigTab 制作点阵/添加图片完成后）
  syncNow: () => syncImageLibraryToNpz(imageList.value),
  addImageItemFromConfig,
  isDrawerOpen: () => imageSelectionDrawerRef.value?.isDrawerOpen?.() || false,
  setImageClickOffsetAreaFromSelection: (rect) =>
    imageSelectionDrawerRef.value?.setClickOffsetAreaFromSelection?.(rect),
});
</script>

<style scoped>
.image-library-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.file-input {
  margin-bottom: 6px;
  flex-shrink: 0;
}

.image-table {
  flex: 1;
  min-height: 0;
}

.image-table :deep(.el-table--border::after),
.image-table :deep(.el-table--border::before) {
  display: none;
}

.image-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.image-table :deep(.el-table td.el-table__cell),
.image-table :deep(.el-table th.el-table__cell) {
  border-right: none;
}

.thumb-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-image {
  width: 56px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.18);
}

.name-cell {
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.name-cell:hover {
  background: #f1f5f9;
}

.name-edit-cell {
  display: flex;
  align-items: center;
}

.name-header-with-filter {
  display: flex;
  align-items: center;
  gap: 6px;
}

.name-filter-input {
  width: 80px;
}

.name-filter-input :deep(.el-input__wrapper) {
  padding: 0 8px;
}

.action-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.size-cell {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 11px;
  color: #64748b;
}

.test-dialog-body {
  display: flex;
  flex-direction: column;
  height: 520px;
}

.template-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  font-size: 12px;
  color: #334155;
}

.template-name {
  font-weight: 500;
}

.template-size {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 11px;
  color: #64748b;
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
}

.result-section {
  flex: 1;
  min-height: 120px;
  max-height: 380px;
  overflow: hidden;
  display: flex;
  flex-direction: row;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  background: #0f172a;
  background-image:
    linear-gradient(45deg, #1e293b 25%, transparent 25%),
    linear-gradient(-45deg, #1e293b 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #1e293b 75%),
    linear-gradient(-45deg, transparent 75%, #1e293b 75%);
  background-size: 12px 12px;
  background-position: 0 0, 0 6px, 6px -6px, -6px 0px;
}

.result-cell {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.result-label {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 4px;
  line-height: 1.35;
}

.result-image {
  flex: 1;
  min-height: 140px;
  width: 100%;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(15, 23, 42, 0.6);
}
</style>