<template>
  <div class="config-tab-container">
    <!-- 配置 JSON 文件选择 -->
    <div>
      <el-input
        v-model="configForm.configPath"
        placeholder="请选择配置 JSON 文件"
        readonly
        size="small"
      >
        <template #prepend>
          <el-button @click="handleSelectConfigFile">选择文件</el-button>
        </template>
        <template #append>
          <el-button @click="handleOpenConfigFile" :disabled="!configForm.configPath">
            打开文件
          </el-button>
        </template>
      </el-input>
    </div>
    <div style="flex: 1; overflow: auto">
      <vue-json-pretty v-if="data" deep="1" :data="data" showIcon :collapsedOnClickBrackets="false">
        <template #renderNodeValue="{ node, defaultValue }">
          <span v-if="node.key == '类型'">{{ node.content }}</span>
          <el-input
            v-else-if="node.key == '偏移点击区域'"
              style=" width: 90%"
              v-model="node.content"
              size="small"
              @blur="handleBlur(node)"
          >
            <template #append>
              <el-button
                :type="
                  isFontClickOffsetAreaSelectionActiveForNode(node)
                    ? 'warning'
                    : 'primary'
                "
                :disabled="!hasSelectionRect"
                size="small"
                @click="toggleFontClickOffsetAreaSelectionForNode(node)"
              >
                {{
                  isFontClickOffsetAreaSelectionActiveForNode(node) ? "取消" : "圈选"
                }}
              </el-button>
            </template>
          </el-input>
          <el-input
            v-else
              style="display: inline-block; width: 90%"
              v-model="node.content"
              size="small"
              @blur="handleBlur(node)"
          />
        </template>
        <template #renderNodeActions="{ node, defaultActions }">
          <template
            v-if="
              node.type != 'content' &&
              node.type != 'arrayStart' &&
              node.level != 0 &&
              node.key != '滑动区域' &&
              node.key != '识字区域' &&
              node.key != '按钮' &&
              node.key != '状态'
            "
          >
            <el-button type="primary" size="small" @click="handleTest(node)"
              >测试</el-button
            >
            <el-button  type="primary" size="small" @click="handleAddConfig(node)"
              >制作点阵/添加图片</el-button
            >
          </template>

          <el-button
            v-if="
              (node.type == 'objectStart' || node.level == 3 || node.level == 1) &&
              node.level != 0 &&
              node.key != '滑动区域' &&
              node.key != '识字区域' &&
              node.key != '按钮' &&
              node.key != '状态'
            "
            type="danger"
            size="small"
            @click="handleDelete(node)"
            >删除</el-button
          >

          <el-button
            v-if="node.key == '滑动区域'"
            type="primary"
            size="small"
            @click="handleAddSliderArea(node)"
            >添加</el-button
          >
          <el-button
            v-if="node.key == '识字区域'"
            type="primary"
            size="small"
            @click="handleAddSzArea(node)"
            >添加</el-button
          >
          <el-button
            v-if="node.key == '状态' || node.key == '按钮' || node.path == 'root'"
            type="primary"
            size="small"
            @click="handleAddItem(node)"
            >添加</el-button
          >
        </template>
      </vue-json-pretty>
    </div>

    <!-- 测试弹框：按当前配置项名称（点阵名）查询所有同名点阵进行找字测试 -->
    <el-dialog
      v-model="testDialogVisible"
      title="找字测试"
      width="420px"
      destroy-on-close
      :close-on-click-modal="false"
      class="config-test-dialog"
      @closed="onTestDialogClosed"
    >
      <FontLibraryMatchDebug
        v-if="testDialogVisible"
        :current-device-id="currentDeviceId"
        :font-library-list="fontLibraryList"
        :initial-font-library-name="testFontLibraryName"
        :initial-similarity="testSimilarity"
        :initial-region="testRegion"
      />
    </el-dialog>

    <transition name="config-drawer-slide">
      <div v-if="drawer" class="config-drawer-wrapper">
        <div class="config-drawer-mask" @click="drawer = false"></div>
        <div class="config-drawer">
          <div class="config-drawer-header">
            <div class="config-drawer-title-wrap">
              <div class="config-drawer-title-main">
                <span class="config-drawer-title">添加字库配置</span>
              </div>
              <div class="config-drawer-subtitle">
                基于当前图片与圈选区域生成字库点阵配置
              </div>
            </div>
            <el-button link type="primary" size="small" @click="drawer = false">
              关闭
            </el-button>
          </div>
          <div class="config-drawer-body">
            <!-- 颜色表格 -->
            <div class="color-table-wrap">
              <el-table
                :data="selectedColors"
                height="150"
                size="small"
                empty-text="请在图片上点击选取颜色"
                :header-cell-style="{
                  background: '#f8fafc',
                  color: '#64748b',
                  fontSize: '11px',
                  fontWeight: 600,
                  borderBottom: '1px solid #e2e8f0',
                }"
                :cell-style="{ fontSize: '12px', padding: '4px 0' }"
                :row-style="{ transition: 'background 0.15s' }"
              >
                <el-table-column label="HEX" width="84">
                  <template #default="scope">
                    <div
                      class="hex-cell"
                      :style="{
                        backgroundColor:
                          '#' + String(scope.row.hex || '').replace(/^#/, ''),
                        color: isLightColor(scope.row.hex) ? '#1e293b' : '#f8fafc',
                      }"
                    >
                      {{ scope.row.hex }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="偏色" min-width="120">
                  <template #default="scope">
                    <div class="slider-cell">
                      <el-slider
                        :model-value="getRowDeviation(scope.$index)"
                        :min="0"
                        :max="100"
                        :show-tooltip="true"
                        @update:model-value="(v) => setRowDeviation(scope.$index, v)"
                      />
                      <span class="slider-value">{{
                        getRowDeviation(scope.$index)
                      }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="" width="40" fixed="right">
                  <template #default="scope">
                    <el-button
                      type="danger"
                      link
                      size="small"
                      @click="handleRemoveColor(scope.$index)"
                      class="delete-btn"
                    >
                      <el-icon>
                        <Close />
                      </el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="table-footer">
                <span class="table-count">{{ selectedColors.length }} 个颜色</span>
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="handleClearAllColors"
                  :disabled="!selectedColors.length"
                  >清空</el-button
                >
              </div>
            </div>

            <!-- 二值化预览 -->
            <div class="result-section">
              <el-image
                v-if="processedImageUrl"
                :src="processedImageUrl"
                :preview-src-list="[processedImageUrl]"
                fit="contain"
                preview-teleported
                style="height: 100%; width: 100%"
              />
              <div v-else class="result-placeholder">
                <el-icon :size="20" style="opacity: 0.3; margin-bottom: 4px">
                  <Picture />
                </el-icon>
                偏色二值化预览
              </div>
            </div>

            <div class="font-config-section">
              <div class="font-row">
                <span class="font-label">是否裁剪</span>
                <div class="font-field">
                  <el-checkbox v-model="enableAutoCrop" size="small" />
                </div>
              </div>
              <div class="font-row">
                <span class="font-label">偏移点击区域</span>
                <div class="font-field">
                  <el-input
                    v-model="fontClickOffsetAreaInput"
                    placeholder="偏移点击区域 x,y,w,h（可选）"
                    size="small"
                    clearable
                  >
                    <template #append>
                      <el-button
                        :type="
                          isDrawerFontClickOffsetAreaSelectionActive
                            ? 'warning'
                            : 'primary'
                        "
                        :disabled="!hasSelectionRect"
                        size="small"
                        @click="toggleFontClickOffsetAreaSelection"
                      >
                        {{
                          isDrawerFontClickOffsetAreaSelectionActive ? "取消" : "圈选"
                        }}
                      </el-button>
                    </template>
                  </el-input>
                </div>
              </div>
            </div>
          </div>
          <div class="config-drawer-footer">
            <el-button
              type="primary"
              size="small"
              @click="handleConfirmAddConfig"
              :disabled="!processedImageUrl"
            >
              确认添加
            </el-button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import VueJsonPretty from "vue-json-pretty";
import "vue-json-pretty/lib/styles.css";
import { ref, watch, onMounted, computed, h } from "vue";
import { ElMessage, ElMessageBox, ElInput, ElCheckbox, ElRadio, ElRadioGroup } from "element-plus";
import { Close, Picture } from "@element-plus/icons-vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import FontLibraryMatchDebug from "./FontLibraryMatchDebug.vue";
const props = defineProps({
  currentImage: {
    type: Object,
    default: null,
  },
  selectionRect: {
    type: Object,
    default: null,
  },
  fontLibraryList: {
    type: Array,
    default: () => [],
  },
  currentDeviceId: {
    type: String,
    default: "",
  },
});

const testDialogVisible = ref(false);
const testFontLibraryName = ref("");
const testSimilarity = ref(undefined);
const testRegion = ref("");

const emit = defineEmits([
  "start-code-generator-selection",
  "stop-code-generator-selection",
  "add-font-library",
  "add-image-to-library",
  "delete-library-resource",
  "open-image-test",
]);

const data = ref(undefined);

watch(
  data,
  (newVal) => {
    autoSaveConfigFile();
  },
  { deep: true }
);

const configForm = ref({
  configPath: "",
});
const selectedConfigPath = ref("");

// 自动保存当前配置到文件（无提示）
const autoSaveConfigFile = async () => {
  if (!configForm.value.configPath) {
    return;
  }

  try {
    const content = JSON.stringify(data.value, null, 2);
    await ipc.invoke(ipcApiRoute.writeTextFile, {
      filePath: configForm.value.configPath,
      content,
    });
  } catch (error) {
    console.error("自动保存配置文件失败:", error);
  }
};

// 选择配置 JSON 文件并加载到 data.value
const handleSelectConfigFile = async () => {
  try {
    const dialogResult = await ipc.invoke(ipcApiRoute.openFileDialog, {
      title: "选择配置 JSON 文件",
      defaultPath: configForm.value.configPath || "",
      filters: [
        { name: "JSON 文件", extensions: ["json"] },
        { name: "所有文件", extensions: ["*"] },
      ],
    });

    if (
      !dialogResult ||
      !dialogResult.success ||
      dialogResult.canceled ||
      !dialogResult.filePath
    ) {
      return;
    }

    const filePath = dialogResult.filePath;
    const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
      filePath,
    });

    if (!readResult || !readResult.success) {
      throw new Error(readResult?.message || "读取文件失败");
    }

    let parsed;
    try {
      parsed = JSON.parse(readResult.content || "{}");
    } catch (e) {
      ElMessage.error("配置文件不是有效的 JSON");
      return;
    }

    data.value = parsed;
    configForm.value.configPath = filePath;
    selectedConfigPath.value = filePath;
    await saveConfigPathToDB();
    ElMessage.success("配置已加载");
  } catch (error) {
    console.error("选择或读取配置文件失败:", error);
    ElMessage.error("选择或读取配置文件失败: " + (error.message || "未知错误"));
  }
};

// 打开当前配置文件
const handleOpenConfigFile = async () => {
  if (!configForm.value.configPath) {
    ElMessage.warning("请先选择配置文件");
    return;
  }

  try {
    const result = await ipc.invoke(ipcApiRoute.openFile, {
      filePath: configForm.value.configPath,
    });

    if (!result || !result.success) {
      throw new Error(result?.message || "打开文件失败");
    }

    ElMessage.success("文件已打开");
  } catch (error) {
    console.error("打开配置文件失败:", error);
    ElMessage.error("打开配置文件失败: " + (error.message || "未知错误"));
  }
};

// 保存配置文件路径到数据库（复用全局的 configPath 字段）
const saveConfigPathToDB = async () => {
  try {
    await ipc.invoke(ipcApiRoute.savePaths, {
      configPath: configForm.value.configPath,
    });
  } catch (error) {
    console.error("保存配置路径失败:", error);
  }
};

// 从数据库加载配置文件路径并自动读取
const loadConfigPathFromDB = async () => {
  try {
    const result = await ipc.invoke(ipcApiRoute.getPaths);
    if (result && result.success && result.data && result.data.configPath) {
      configForm.value.configPath = result.data.configPath;
      selectedConfigPath.value = result.data.configPath;
      await loadConfigFile(result.data.configPath);
    }
  } catch (error) {
    console.error("加载配置路径失败:", error);
  }
};

// 读取指定配置文件到 data.value
const loadConfigFile = async (filePath) => {
  if (!filePath) return;

  try {
    const readResult = await ipc.invoke(ipcApiRoute.readTextFile, {
      filePath,
    });

    if (!readResult || !readResult.success) {
      return;
    }

    try {
      const parsed = JSON.parse(readResult.content || "{}");
      data.value = parsed;
    } catch (e) {
      console.error("解析配置 JSON 失败:", e);
    }
  } catch (error) {
    console.error("加载配置文件失败:", error);
  }
};

// data 变化时 key 变化，强制 Cascader 重新挂载，使 level 1 选项随 data 更新
const cascaderOptionsKey = computed(() =>
  JSON.stringify(Object.keys(data.value || {}).sort())
);

const cascaderProps = {
  lazy: true,
  lazyLoad(node, resolve) {
    const { level } = node;
    if (level === 0) {
      resolve([
        { value: "界面", label: "界面", leaf: true },
        { value: "按钮(固定区域)", label: "按钮(固定区域)" },
        { value: "按钮(点阵识别)", label: "按钮(点阵识别)" },
        { value: "状态", label: "状态" },
      ]);
    }
    if (level === 1) {
      resolve(
        Object.keys(data.value || {}).map((item) => ({
          value: item,
          label: item,
          leaf: true,
        }))
      );
    }
  },
};

const drawer = ref(false);
const currentNode = ref(null);

const selectedCascader = ref([]);
const selectedName = ref("");

// data 变化时清空级联选择，避免选中项与当前选项不一致
watch(cascaderOptionsKey, () => {
  selectedCascader.value = [];
});

// ========== 独立的颜色管理 ==========
const selectedColors = ref([]); // 自己维护的颜色列表 [{ hex: 'D61E24' }, ...]
const rowDeviations = ref([]); // 每行偏色值 0–100

const processedImageUrl = ref(null);
const enableAutoCrop = ref(true);
const fontClickOffsetAreaInput = ref("");

// 偏移点击区域圈选状态
const fontClickOffsetAreaSelectionEnabled = ref(false);

// 偏移点击区域圈选目标：
// - drawer：写回 `fontClickOffsetAreaInput`（抽屉里添加点阵）
// - json：写回 vue-json-pretty 对应节点的 `node.content`（通过 node.path 精确定位）
const offsetAreaSelectionTargetMode = ref("drawer"); // "drawer" | "json"
const offsetAreaSelectionTargetNodePath = ref("");

const isDrawerFontClickOffsetAreaSelectionActive = computed(() => {
  return (
    fontClickOffsetAreaSelectionEnabled.value &&
    offsetAreaSelectionTargetMode.value === "drawer"
  );
});

// 是否存在左侧圈选范围（用于偏移点击区域的基准）
const hasSelectionRect = computed(() => {
  return props.selectionRect && props.selectionRect.w && props.selectionRect.h;
});


const handleBlur = (node) => {
  const keys = getPathKeys(node.path);

  if (!keys.length) return;

  // 找到当前字段的原始值
  let target = data.value;
  keys.forEach((key, index) => {
    if (index < keys.length - 1) {
      target = target[key];
    }
  });
  const lastKey = keys[keys.length - 1];
  const oldValue = target?.[lastKey];
  const oldStr = oldValue == null ? "" : String(oldValue);
  const newStr = node.content == null ? "" : String(node.content);

  // 未修改，直接返回
  if (newStr === oldStr) {
    return;
  }

  const trimmed = newStr.trim();

  // ===== 按字段校验 =====
  // 1. 含“区域”的字段：允许空，或 x,y,w,h 四个整数
  if ((node.key && String(node.key).includes("区域")) || keys.join("").includes("区域")) {
    if (trimmed !== "" && !/^-?\d+,-?\d+,-?\d+,-?\d+$/.test(trimmed)) {
      ElMessage.error("区域格式错误，应为空或 x,y,w,h");
      node.content = oldStr;
      return;
    }
  }

  // 2. 偏色：D61E24-373737|D61E24-373731 形式，即 6位HEX-6位HEX，用 | 分割
  if (node.key === "偏色") {
    const pattern = /^([0-9A-Fa-f]{6}-[0-9A-Fa-f]{6})(\|[0-9A-Fa-f]{6}-[0-9A-Fa-f]{6})*$/;
    if (trimmed !== "" && !pattern.test(trimmed)) {
      ElMessage.error("偏色格式错误，应为 6位HEX-6位HEX，多个用“|”分隔");
      node.content = oldStr;
      return;
    }
  }

  // 3. 相似度：只能在 0~1 之间，最多 2 位小数
  let valueToSave = newStr;
  if (node.key === "相似度") {
    if (trimmed === "") {
      ElMessage.error("相似度不能为空");
      node.content = oldStr;
      return;
    }
    const num = Number(trimmed);
    if (Number.isNaN(num) || num < 0 || num > 1) {
      ElMessage.error("相似度必须在 0 到 1 之间，最多 2 位小数");
      node.content = oldStr;
      return;
    }
    const parts = trimmed.split(".");
    if (parts[1] && parts[1].length > 2) {
      ElMessage.error("相似度最多保留 2 位小数");
      node.content = oldStr;
      return;
    }
    valueToSave = num; // 相似度保存为数值
  }

  // 通过校验，保存并提示
  target[lastKey] = valueToSave;
  ElMessage.success("保存成功");
};

// 供外部（图片点击）调用的添加颜色方法
const addColor = (colorInfo) => {
  if (!colorInfo || !colorInfo.hex) return;
  const hex = colorInfo.hex.replace(/^#/, "").toUpperCase();
  // 检查是否已存在相同颜色
  if (selectedColors.value.some((c) => c.hex === hex)) {
    ElMessage.warning("已存在相同颜色");
    return;
  }
  selectedColors.value.push({ hex });
  rowDeviations.value.push(0);
  // 重新计算二值化
  if (props.currentImage?.url) runBinarizationFromTable();
};

// 删除颜色
const handleRemoveColor = (index) => {
  selectedColors.value.splice(index, 1);
  rowDeviations.value.splice(index, 1);
  if (selectedColors.value.length > 0 && props.currentImage?.url) {
    runBinarizationFromTable();
  } else {
    processedImageUrl.value = null;
  }
};

// 清空所有颜色
const handleClearAllColors = () => {
  selectedColors.value = [];
  rowDeviations.value = [];
  processedImageUrl.value = null;
  ElMessage.success("已清空全部颜色");
};

const handleAddSliderArea = (node) => {
  currentNode.value = getCurrentNode(node);
  
  ElMessageBox.prompt("", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    inputPlaceholder: "请输入滑动区域名称",
  }).then(({ value }) => {
    if (!value || !value.trim()) {
      ElMessage.error("滑动区域名称不能为空");
      return;
    }
    if (Object.prototype.hasOwnProperty.call(currentNode.value, value.trim())) {
      ElMessage.error("名称已存在");
      return;
    }
    currentNode.value[value.trim()] = {
      起始区域: "",
      结束区域: "",
    };
  });
};

// 添加识字区域
const handleAddSzArea = (node) => {
  currentNode.value = getCurrentNode(node);
  ElMessageBox.prompt("", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    inputPlaceholder: "请输入识字区域名称",
  }).then(({ value }) => {
    if (!value || !value.trim()) {
      ElMessage.error("识字区域名称不能为空");
      return;
    }
    if (Object.prototype.hasOwnProperty.call(currentNode.value, value.trim())) {
      ElMessage.error("名称已存在");
      return;
    }
    currentNode.value[value.trim()] = ''
  });
};
const handleAddItem = (node) => {
  let itemNode = {};
  if (node.path == "root") {
    itemNode = data.value;
  } else {
    currentNode.value = getCurrentNode(node);
    itemNode = currentNode.value;
    
  }
  // 类型（仅按钮需要）：固定区域 / 点阵 / 图片
  const type = ref("图片");
  // 名字
  const name = ref("");

  const content = () =>
    h(
      "div",
      {
        style: "display:flex;flex-direction:column;gap:12px;",
      },
      [
        node.key === "按钮"
          ? h(
              "div",
              {
                style: "display:flex;align-items:center;gap:8px;",
              },
              [
                h(
                  "span",
                  {
                    style: "width:80px;text-align:right;",
                  },
                  "类型："
                ),
                h(
                  ElRadioGroup,
                  {
                    modelValue: type.value,
                    "onUpdate:modelValue": (val) => {
                      type.value = val;
                    },
                  },
                  () => [
                    h(
                      ElRadio,
                      { label: "固定区域" },
                      () => "固定区域"
                    ),
                    h(
                      ElRadio,
                      { label: "点阵" },
                      () => "点阵"
                    ),
                    h(
                      ElRadio,
                      { label: "图片" },
                      () => "图片"
                    ),
                  ]
                ),
              ]
            )
          : h(
              "div",
              {
                style: "display:flex;align-items:center;gap:8px;",
              },
              [
                h(
                  "span",
                  {
                    style: "width:80px;text-align:right;",
                  },
                  "类型："
                ),
                h(
                  ElRadioGroup,
                  {
                    modelValue: type.value,
                    "onUpdate:modelValue": (val) => {
                      type.value = val;
                    },
                  },
                  () => [
                    h(
                      ElRadio,
                      { label: "点阵" },
                      () => "点阵"
                    ),
                    h(
                      ElRadio,
                      { label: "图片" },
                      () => "图片"
                    ),
                  ]
                ),
              ]
            ),
        h(
          "div",
          {
            style: "display:flex;align-items:center;gap:8px;",
          },
          [
            h(
              "span",
              {
                style: "width:80px;text-align:right;flex-shrink:0;",
              },
              "配置名称："
            ),
            h(ElInput, {
              modelValue: name.value,
              "onUpdate:modelValue": (val) => {
                name.value = val;
              },
              placeholder: "请输入名称",
            }),
          ]
        ),
      ]
    );

  ElMessageBox({
    title: "添加配置项",
    message: content,
    showCancelButton: true,
    confirmButtonText: "确定",
    cancelButtonText: "取消",
  })
    .then(() => {
      const key = name.value.trim();
      if (!key) {
        ElMessage.error("名称不能为空");
        return;
      }
      if (Object.prototype.hasOwnProperty.call(itemNode, key)) {
        ElMessage.error("名称已存在");
        return;
      }

      if (node.path == "root") {
          itemNode[key] = {
            类型: type.value,
            查找区域: "",
            相似度: 0.9,
            状态: {},
            按钮: {},
            滑动区域: {},
            识字区域: {},
            误触区域: ""
          };
        } else if (type.value === "固定区域") {
          itemNode[key] = {
            类型: type.value,
            固定点击区域: ""
          };
        } else {
          itemNode[key] = {
            类型: type.value,
            查找区域: "",
            偏移点击区域: "",
            相似度: 0.9,
          };
        }
    })
    .catch(() => {});
};

// 获取当前节点
const getCurrentNode = (node) => {
  const keys = getPathKeys(node.path);
  
  if (keys.length == 1) {
    return data.value[keys[0]];
  }

  if (keys.length == 2) {
    return data.value[keys[0]][keys[1]];
  }

  if (keys.length == 3) {
    return data.value[keys[0]][keys[1]][keys[2]];
  }

  if (keys.length == 4) {
    return data.value[keys[0]][keys[1]][keys[2]][keys[3]];
  }

};
const currentName = ref("");
// ========== 节点操作 ==========
const handleAddConfig = (node) => {
  currentNode.value = getCurrentNode(node);
  const keys = getPathKeys(node.path);
  currentName.value = keys.join("_");
  if (currentNode.value.类型 == "图片") {
    // 图片类型：将当前图片或圈选区域添加到图片库（由右侧面板统一处理）
    if (!props.currentImage || !props.currentImage.url) {
      ElMessage.warning("当前没有图片，无法添加到图片库");
      return;
    }
    emit("add-image-to-library", {
      name: currentName.value,
      selectionRect: props.selectionRect || null,
      currentImageUrl: props.currentImage.url,
    });
    return;
  }
  if (currentNode.value.类型 == "点阵") {
    fontClickOffsetAreaInput.value = "";
    // 重置 drawer 状态（保留已有的颜色列表，方便连续操作）
    enableAutoCrop.value = true;
    drawer.value = true;
  }

};

// 切换偏移点击区域圈选模式
const toggleFontClickOffsetAreaSelection = () => {
  if (!hasSelectionRect.value) {
    ElMessage.warning("请先在左侧进行圈选，才能使用偏移点击区域功能");
    return;
  }

  // 当前选择目标就是抽屉输入框：取消
  if (isDrawerFontClickOffsetAreaSelectionActive.value) {
    fontClickOffsetAreaSelectionEnabled.value = false;
    offsetAreaSelectionTargetMode.value = "drawer";
    offsetAreaSelectionTargetNodePath.value = "";
    emit("stop-code-generator-selection");
    ElMessage.info("已取消圈选模式");
  } else {
    // 若已开启但目标在 json：切换为抽屉目标（继续圈选）
    if (fontClickOffsetAreaSelectionEnabled.value) {
      offsetAreaSelectionTargetMode.value = "drawer";
      offsetAreaSelectionTargetNodePath.value = "";
      ElMessage.info("已切换偏移点击区域圈选目标");
      return;
    }

    // 未开启：开始圈选
    fontClickOffsetAreaSelectionEnabled.value = true;
    offsetAreaSelectionTargetMode.value = "drawer";
    offsetAreaSelectionTargetNodePath.value = "";
    // 使用单独的类型标识，区分与颜色 Tab 的偏移点击区域
    emit("start-code-generator-selection", "configFontClickOffsetArea");
    ElMessage.info("请在图片上圈选偏移点击区域");
  }
};

const isFontClickOffsetAreaSelectionActiveForNode = (node) => {
  return (
    fontClickOffsetAreaSelectionEnabled.value &&
    offsetAreaSelectionTargetMode.value === "json" &&
    offsetAreaSelectionTargetNodePath.value === node?.path
  );
};

// 给 vue-json-pretty 中“偏移点击区域”节点用：点击“圈选”后在图片上拖拽获取偏移值
const toggleFontClickOffsetAreaSelectionForNode = (node) => {
  if (!hasSelectionRect.value) {
    ElMessage.warning("请先在左侧进行圈选，才能使用偏移点击区域功能");
    return;
  }
  if (!node?.path) return;

  const targetIsActive = isFontClickOffsetAreaSelectionActiveForNode(node);

  // 已开启且点击当前节点：取消
  if (targetIsActive) {
    fontClickOffsetAreaSelectionEnabled.value = false;
    offsetAreaSelectionTargetMode.value = "drawer";
    offsetAreaSelectionTargetNodePath.value = "";
    emit("stop-code-generator-selection");
    ElMessage.info("已取消圈选模式");
    return;
  }

  // 若已开启但目标不是当前节点：切换目标（继续圈选）
  if (fontClickOffsetAreaSelectionEnabled.value) {
    offsetAreaSelectionTargetMode.value = "json";
    offsetAreaSelectionTargetNodePath.value = node.path;
    ElMessage.info("已切换偏移点击区域圈选目标");
    return;
  }

  // 未开启：开始圈选
  fontClickOffsetAreaSelectionEnabled.value = true;
  offsetAreaSelectionTargetMode.value = "json";
  offsetAreaSelectionTargetNodePath.value = node.path;
  emit("start-code-generator-selection", "configFontClickOffsetArea");
  ElMessage.info("请在图片上圈选偏移点击区域");
};

// ========== 偏色管理 ==========
const getRowDeviation = (index) => rowDeviations.value[index] ?? 0;
const setRowDeviation = (index, value) => {
  const arr = [...rowDeviations.value];
  arr[index] = Math.max(0, Math.min(100, value));
  rowDeviations.value = arr;
  runBinarizationFromTable();
};

// ========== 工具函数 ==========
const isLightColor = (hex) => {
  hex = String(hex).replace("#", "");
  if (hex.length === 3)
    hex = hex
      .split("")
      .map((c) => c + c)
      .join("");
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 186;
};

const hexToRgb = (hex) => {
  hex = hex.replace("#", "");
  if (hex.length === 3)
    hex = hex
      .split("")
      .map((c) => c + c)
      .join("");
  return {
    r: parseInt(hex.substring(0, 2), 16),
    g: parseInt(hex.substring(2, 4), 16),
    b: parseInt(hex.substring(4, 6), 16),
  };
};

const numToHex = (num) => {
  const hex = Math.max(0, Math.min(255, Math.floor(num)))
    .toString(16)
    .toUpperCase();
  return hex.length === 1 ? "0" + hex : hex;
};

// ========== 偏色计算 ==========
const buildDeviationListFromTable = () => {
  const list = [];
  for (let i = 0; i < selectedColors.value.length; i++) {
    const d = rowDeviations.value[i] ?? 0;
    const baseRgb = hexToRgb(selectedColors.value[i].hex);
    const baseHex = numToHex(baseRgb.r) + numToHex(baseRgb.g) + numToHex(baseRgb.b);
    const deviationHex = numToHex(d) + numToHex(d) + numToHex(d);
    list.push(`${baseHex}-${deviationHex}`);
  }
  return list;
};

const parseDeviation = (deviationStr) => {
  const [baseHex, deviationHex] = deviationStr.split("-");
  if (!baseHex || !deviationHex || baseHex.length !== 6 || deviationHex.length !== 6)
    return null;
  return {
    base: {
      r: parseInt(baseHex.substring(0, 2), 16),
      g: parseInt(baseHex.substring(2, 4), 16),
      b: parseInt(baseHex.substring(4, 6), 16),
    },
    deviation: {
      r: parseInt(deviationHex.substring(0, 2), 16),
      g: parseInt(deviationHex.substring(2, 4), 16),
      b: parseInt(deviationHex.substring(4, 6), 16),
    },
  };
};

const isColorInDeviationRange = (r, g, b, deviationData) => {
  const { base, deviation } = deviationData;
  return (
    r >= Math.max(0, base.r - deviation.r) &&
    r <= Math.min(255, base.r + deviation.r) &&
    g >= Math.max(0, base.g - deviation.g) &&
    g <= Math.min(255, base.g + deviation.g) &&
    b >= Math.max(0, base.b - deviation.b) &&
    b <= Math.min(255, base.b + deviation.b)
  );
};

// ========== 二值化处理 ==========
const runBinarizationFromTable = () => {
  if (!props.currentImage?.url) return;
  const deviationList = buildDeviationListFromTable();
  if (deviationList.length === 0) return;
  const deviationDataList = deviationList.map(parseDeviation).filter(Boolean);
  if (deviationDataList.length === 0) return;

  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    try {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      let startX = 0,
        startY = 0,
        width = img.width,
        height = img.height;
      if (props.selectionRect?.w > 0 && props.selectionRect?.h > 0) {
        startX = Math.max(0, Math.min(props.selectionRect.x, img.width - 1));
        startY = Math.max(0, Math.min(props.selectionRect.y, img.height - 1));
        width = Math.min(props.selectionRect.w, img.width - startX);
        height = Math.min(props.selectionRect.h, img.height - startY);
      }
      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(img, startX, startY, width, height, 0, 0, width, height);
      const imageData = ctx.getImageData(0, 0, width, height);
      const pixelData = imageData.data;

      for (let i = 0; i < pixelData.length; i += 4) {
        const r = pixelData[i],
          g = pixelData[i + 1],
          b = pixelData[i + 2];
        let inRange = false;
        for (const dd of deviationDataList) {
          if (isColorInDeviationRange(r, g, b, dd)) {
            inRange = true;
            break;
          }
        }
        pixelData[i] = pixelData[i + 1] = pixelData[i + 2] = inRange ? 255 : 0;
        pixelData[i + 3] = 255;
      }
      ctx.putImageData(imageData, 0, 0);
      processedImageUrl.value = canvas.toDataURL("image/png");
    } catch (e) {
      console.error("二值化出错:", e);
    }
  };
  img.src = props.currentImage.url;
};

// ========== 确认添加配置 ==========
const handleConfirmAddConfig = async () => {
  if (!processedImageUrl.value) {
    ElMessage.warning("请先生成点阵");
    return;
  }

  const deviationList = buildDeviationListFromTable();
  if (!deviationList.length) {
    ElMessage.warning("请先添加颜色");
    return;
  }

  try {
    const img = new Image();
    img.crossOrigin = "anonymous";

    await new Promise((resolve, reject) => {
      img.onload = async () => {
        try {
          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);

          const imageData = ctx.getImageData(0, 0, img.width, img.height);
          const pixelData = imageData.data;

          // 找到白色像素的最小边界框
          let minX = img.width,
            minY = img.height,
            maxX = 0,
            maxY = 0;
          let whitePixelCount = 0;

          for (let y = 0; y < img.height; y++) {
            for (let x = 0; x < img.width; x++) {
              const idx = (y * img.width + x) * 4;
              if (
                pixelData[idx] > 200 &&
                pixelData[idx + 1] > 200 &&
                pixelData[idx + 2] > 200
              ) {
                whitePixelCount++;
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);
              }
            }
          }

          if (whitePixelCount === 0) {
            ElMessage.warning("二值化图片中没有白色像素");
            reject(new Error("没有白色像素"));
            return;
          }

          // 根据是否裁剪决定范围
          let cropMinX, cropMinY, cropMaxX, cropMaxY;
          if (enableAutoCrop.value) {
            cropMinX = minX;
            cropMinY = minY;
            cropMaxX = maxX;
            cropMaxY = maxY;
          } else {
            cropMinX = 0;
            cropMinY = 0;
            cropMaxX = img.width - 1;
            cropMaxY = img.height - 1;
          }

          const width = cropMaxX - cropMinX + 1;
          const height = cropMaxY - cropMinY + 1;

          // 提取二值数据
          const binaryData = [];
          for (let y = cropMinY; y <= cropMaxY; y++) {
            for (let x = cropMinX; x <= cropMaxX; x++) {
              const idx = (y * img.width + x) * 4;
              const isWhite =
                pixelData[idx] > 200 &&
                pixelData[idx + 1] > 200 &&
                pixelData[idx + 2] > 200;
              binaryData.push(isWhite ? "1" : "0");
            }
          }

          // 转为十六进制点阵字符串
          let matrixHex = "";
          for (let i = 0; i < binaryData.length; i += 4) {
            const bits = binaryData.slice(i, i + 4).join("");
            const paddedBits = bits.padEnd(4, "0");
            matrixHex += parseInt(paddedBits, 2).toString(16).toUpperCase();
          }

          // 偏色列表以 "|" 组合
          const deviationStr = deviationList.join("|");
          // 点阵 = hex&width,height,count
          const matrixStr = `${matrixHex}&${width},${height},${whitePixelCount}`;
          
          // 处理偏移点击区域，格式为 x,y,w,h，若未填写则默认 0,0,0,0
          let clickOffsetArea = "0,0,0,0";
          if (fontClickOffsetAreaInput.value && fontClickOffsetAreaInput.value.trim()) {
            const raw = fontClickOffsetAreaInput.value.trim();
            const parts = raw.split(",").map((s) => s.trim());
            if (
              parts.length !== 4 ||
              parts.some((p) => p === "" || Number.isNaN(parseInt(p, 10)))
            ) {
              ElMessage.warning("偏移点击区域格式不正确，应为：x,y,w,h");
              reject(new Error("偏移点击区域格式不正确"));
              return;
            }
            const [x, y, w, h] = parts.map((p) => parseInt(p, 10));
            if (w < 0 || h < 0) {
              ElMessage.warning("偏移点击区域宽高必须为非负整数");
              reject(new Error("偏移点击区域宽高必须为非负整数"));
              return;
            }
            clickOffsetArea = `${x},${y},${w},${h}`;
          }

          // 使用 currentName 作为字库名称
          const name = (currentName.value || "").trim();

          if (name) {
            const fontItem = {
              id: Date.now(),
              matrix: matrixHex,
              width,
              height,
              totalCount: whitePixelCount,
              sizeInfo: `${width}×${height} (${whitePixelCount})`,
              deviation: deviationStr,
              name,
              clickOffsetArea,
              editing: false,
              binaryData,
            };

            const addPromise = new Promise((resolveAdd) => {
              emit("add-font-library", fontItem, resolveAdd);
            });

            await addPromise;
          } else {
            ElMessage.warning("点阵名称为空，未加入字库，仅更新配置");
          }

          // ElMessage.success(`配置 添加成功`);
          drawer.value = false;
          resolve();
        } catch (error) {
          console.error("处理点阵时出错:", error);
          reject(error);
        }
      };
      img.onerror = () => reject(new Error("加载图片失败"));
      img.src = processedImageUrl.value;
    });
  } catch (error) {
    console.error("添加配置失败:", error);
    ElMessage.error("添加配置失败: " + (error.message || "未知错误"));
  }
};

// 通过圈选结果设置偏移点击区域（由父组件调用）
const setFontClickOffsetAreaFromSelection = (rect) => {
  if (!rect || !rect.w || !rect.h) {
    return;
  }

  // 偏移点击区域需要基于左侧圈选范围计算偏移值
  if (!props.selectionRect || !props.selectionRect.w || !props.selectionRect.h) {
    ElMessage.warning("请先在左侧进行圈选，然后再圈选偏移点击区域");
    // 不取消圈选模式，让用户可以继续操作
    return;
  }

  // 计算偏移值：偏移点击区域的坐标 - 左侧圈选范围的坐标
  const offsetX = rect.x - props.selectionRect.x;
  const offsetY = rect.y - props.selectionRect.y;
  const areaStr = `${offsetX},${offsetY},${rect.w},${rect.h}`;

  if (offsetAreaSelectionTargetMode.value === "drawer") {
    fontClickOffsetAreaInput.value = areaStr;
  } else {
    // 写回到 vue-json-pretty 对应节点的 `data.value` 上
    const keys = getPathKeys(offsetAreaSelectionTargetNodePath.value);
    if (!keys.length) {
      ElMessage.warning("无法定位偏移点击区域节点，已生成偏移值但未写回");
    } else {
      let target = data.value;
      for (let i = 0; i < keys.length - 1; i++) {
        target = target?.[keys[i]];
      }
      const lastKey = keys[keys.length - 1];
      if (target && Object.prototype.hasOwnProperty.call(target, lastKey)) {
        target[lastKey] = areaStr;
      } else {
        // 兜底：尝试写入
        try {
          target[lastKey] = areaStr;
        } catch (e) {
          ElMessage.warning("无法写回偏移点击区域节点值");
        }
      }
    }
  }
  ElMessage.success("已获取偏移点击区域范围（已计算偏移值）");

  // 自动取消圈选模式
  fontClickOffsetAreaSelectionEnabled.value = false;
  emit("stop-code-generator-selection");
  offsetAreaSelectionTargetMode.value = "drawer";
  offsetAreaSelectionTargetNodePath.value = "";
};

/** 从 node.path 解析出键路径，如 "主界面"."按钮"."某名称" -> ['主界面','按钮','某名称'] */
// root.abc["123"].ddd.ccc['nihao'], ['abc', '123', 'ddd', 'ccc', 'nihao']
const getPathKeys = (path) => {
  if (!path || typeof path !== "string") return [];
  // 支持点语法与括号(单引号/双引号)
  const keys = path
    .replace(/\[(["'`])([^\1]+?)\1\]/g, '.$2') // 把[...](单双引号)转为.内容
    .split('.')
    .map(s => s.trim().replace(/^["'`]|["'`]$/g, '')) // 移除两端引号
    .filter(s => s.length > 0 && s !== '');

  // 如果第一个是root则丢掉
  return keys[0] === 'root' ? keys.slice(1) : keys;
};

/** 点击测试：点阵则弹出找字测试弹框；图片则用图片库中同名图片打开模板匹配测试 */
const handleTest = (node) => {
  if (!node || node.key == null) return;

  const path = getPathKeys(node.path);
  let configItem = data.value;
  for (const key of path) {
    configItem = configItem?.[key];
  }

  const name = path.join("_");
  const similarity =
    configItem?.相似度 != null ? Number(configItem.相似度) : undefined;
  const region =
    configItem?.查找区域 != null && configItem.查找区域 !== ""
      ? String(configItem.查找区域).trim()
      : "";

  if (configItem?.类型 === "图片") {
    emit("open-image-test", {
      name,
      similarity,
      region,
    });
    return;
  }

  testFontLibraryName.value = name;
  testSimilarity.value = similarity;
  testRegion.value = region;
  testDialogVisible.value = true;
};

/** 测试弹框关闭时清空初始值 */
const onTestDialogClosed = () => {
  testFontLibraryName.value = "";
  testSimilarity.value = undefined;
  testRegion.value = "";
};

/** 删除节点对应的配置项 */
const handleDelete = (node) => {
  const keys = getPathKeys(node.path);
  if (!keys.length) {
    ElMessage.warning("无法解析节点路径");
    return;
  }
  const keyToDelete = keys[keys.length - 1];
  let parent = data.value;
  for (let i = 0; i < keys.length - 1; i++) {
    parent = parent?.[keys[i]];
  }
  if (parent == null || !Object.prototype.hasOwnProperty.call(parent, keyToDelete)) {
    ElMessage.warning("项不存在或无法删除");
    return;
  }
  const 类型 = parent[keyToDelete]?.类型;
  const nameToDelete = keys.join("_");

  ElMessageBox.confirm(`确定要删除「${keyToDelete}」吗？`, "删除确认", {
    confirmButtonText: "删除",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(() => {
      delete parent[keyToDelete];
      ElMessage.success("已删除");

      if (类型 === "图片" || 类型 === "点阵") {
        ElMessageBox.confirm(`是否删除「${keyToDelete}」对应的资源？`, "删除确认", {
          confirmButtonText: "删除",
          cancelButtonText: "取消",
          type: "warning",
        })
          .then(() => {
            emit("delete-library-resource", { type: 类型, name: nameToDelete });
            ElMessage.success(`${keyToDelete} 对应的资源已删除`);
          })
          .catch(() => {});
      }
    })
    .catch(() => {});
};


onMounted(() => {
  loadConfigPathFromDB();
});

// 暴露给父组件的方法与状态
defineExpose({
  addColor,
  setFontClickOffsetAreaFromSelection,
  /** 是否正在显示「添加字库配置」抽屉，用于在未开启圈选时也允许点击图片选色 */
  isDrawerOpen: () => drawer.value,
});
</script>

<style scoped>
.config-tab-container {
  position: relative;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-sizing: border-box;
  background: #f9fafb;
}

.config-tab-container :deep(.vjs-tree) {
  /* background-color: #ffffff; */
  /* border-radius: 8px; */
  border: 1px solid #e2e8f0;
  gap: 6px !important;
  display: flex;
  flex-direction: column;
  /* padding: 8px 10px; */
  /* font-size: 12px; */
  /* color: #1e293b; */
  /* font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; */
}

.config-tab-container :deep(.vjs-tree-node__content) {
  line-height: 1.5;
}

.config-tab-container :deep(.vjs-tree-node) {
  align-items: center;
}

.config-drawer-wrapper {
  position: absolute;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  z-index: 20;
}

.config-drawer-mask {
  flex: 1;
  background: rgba(15, 23, 42, 0.32);
  backdrop-filter: blur(2px);
}

.config-drawer {
  position: relative;
  height: 100%;
  width: 360px;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  z-index: 1;
  border-left: 1px solid #e2e8f0;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.25);
  border-radius: 8px 0 0 8px;
}

.config-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 8px;
  flex-shrink: 0;
  border-bottom: 1px solid #e2e8f0;
  background: radial-gradient(circle at top left, #e0f2fe 0, #f8fafc 45%, #ffffff 100%);
}

.config-drawer-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.config-drawer-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.config-drawer-title-main {
  display: flex;
  align-items: center;
  gap: 6px;
}

.config-drawer-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #0369a1;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.25);
}

.config-drawer-subtitle {
  font-size: 11px;
  color: #64748b;
}

.config-drawer-body {
  flex: 1;
  padding: 0 5px;
  overflow: auto;
  font-size: 13px;
  color: #475569;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-drawer-footer {
  flex-shrink: 0;
  padding: 8px 14px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

/* 颜色表格 */
.color-table-wrap {
  flex-shrink: 0;
}

.color-table-wrap :deep(.el-table) {
  --el-table-border-color: #e8ecf1;
}

.color-table-wrap :deep(.el-table td.el-table__cell),
.color-table-wrap :deep(.el-table th.el-table__cell) {
  border-right: none;
}

.color-table-wrap :deep(.el-table--border::after),
.color-table-wrap :deep(.el-table--border::before) {
  display: none;
}

.color-table-wrap :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.table-footer {
  padding: 3px 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  background: #fafbfc;
}

.table-count {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
}

.hex-cell {
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.slider-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 8px;
}

.slider-cell :deep(.el-slider) {
  flex: 1;
}

.slider-value {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 10px;
  color: #94a3b8;
  min-width: 20px;
  text-align: right;
}

.delete-btn {
  padding: 2px !important;
}

/* 二值化预览区域 */
.result-section {
  flex: 1;
  min-height: 80px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
  background: #0f172a;
  background-image: linear-gradient(45deg, #1e293b 25%, transparent 25%),
    linear-gradient(-45deg, #1e293b 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #1e293b 75%),
    linear-gradient(-45deg, transparent 75%, #1e293b 75%);
  background-size: 12px 12px;
  background-position: 0 0, 0 6px, 6px -6px, -6px 0px;
}

.result-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  color: #475569;
  font-size: 11px;
  letter-spacing: 0.3px;
  padding: 20px 0;
}

/* 字库配置区 */
.font-config-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 0 4px;
  margin-top: 4px;
  border-top: 1px solid #e2e8f0;
}

.font-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.font-label {
  width: 80px;
  font-size: 12px;
  color: #64748b;
  text-align: right;
  flex-shrink: 0;
}

.font-field {
  flex: 1;
}

/* 过渡动画 */
.config-drawer-slide-enter-from,
.config-drawer-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.config-drawer-slide-enter-active,
.config-drawer-slide-leave-active {
  transition: all 0.25s ease;
}
</style>
