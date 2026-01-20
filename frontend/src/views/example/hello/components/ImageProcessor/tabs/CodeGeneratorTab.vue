<template>
  <div class="code-generator-tab">
    <el-form :model="formData" label-width="95px" size="small">
      <!-- 资源存放路径选择框 -->
      <el-form-item label="资源存放路径" required>
        <el-input v-model="formData.resourcePath" placeholder="请选择资源存放路径" readonly>
          <template #append>
            <el-button @click="handleSelectResourcePath">选择</el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 配置文件选择框 -->
      <el-form-item label="配置文件" required>
        <el-input v-model="formData.configPath" placeholder="请选择配置文件" readonly>
          <template #append>
            <el-button @click="handleSelectConfigPath">选择</el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 图片名输入框 -->
      <el-form-item label="图片名" required>
        <div style="display: flex; gap: 10px; align-items: center;">
          <el-input v-model="formData.imageName" placeholder="请输入图片名称" style="flex: 1;" />
          <el-radio-group v-model="imageSourceType" size="small">
            <el-radio-button label="current">当前大图</el-radio-button>
            <el-radio-button label="transparent">透明图</el-radio-button>
          </el-radio-group>
        </div>
      </el-form-item>

      <!-- 颜色偏色输入框 -->
      <el-form-item label="颜色偏色">
        <el-input v-model="formData.colorDeviation" placeholder="请输入颜色偏色，例如：D7CCC6-0E0E09">
          <template #append>
            <el-button @click="handleGetDeviation">获取偏色</el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 查找区域输入框 -->
      <el-form-item label="查找区域">
        <el-input v-model="formData.searchArea" placeholder="请输入查找区域，格式：x,y,w,h">
          <template #append>
            <el-button :type="codeGeneratorSelectionEnabled === 'searchArea' ? 'warning' : 'primary'"
              @click="toggleCodeGeneratorSelection('searchArea')">
              {{ codeGeneratorSelectionEnabled === 'searchArea' ? '取消圈选范围' : '启动圈选范围' }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 偏移点击区域输入框 -->
      <el-form-item label="偏移点击区域">
        <el-input v-model="formData.clickOffsetArea" placeholder="请输入偏移点击区域，格式：x,y,w,h">
          <template #append>
            <el-button :type="codeGeneratorSelectionEnabled === 'clickOffsetArea' ? 'warning' : 'primary'"
              :disabled="!hasSelectionRect" @click="toggleCodeGeneratorSelection('clickOffsetArea')">
              {{ codeGeneratorSelectionEnabled === 'clickOffsetArea' ? '取消圈选范围' : '启动圈选范围' }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 点击区域输入框 -->
      <el-form-item label="点击区域">
        <el-input v-model="formData.clickArea" placeholder="请输入点击区域，格式：x,y,w,h">
          <template #append>
            <el-button :type="codeGeneratorSelectionEnabled === 'clickArea' ? 'warning' : 'primary'"
              @click="toggleCodeGeneratorSelection('clickArea')">
              {{ codeGeneratorSelectionEnabled === 'clickArea' ? '取消圈选范围' : '启动圈选范围' }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 相似度选择框 -->
      <el-form-item label="相似度">
        <div style="display: flex; align-items: center; width: 100%">
          <el-slider v-model="formData.similarity" :min="0.1" :max="1" :step="0.1" :format-tooltip="formatSimilarity"
            style="flex:1; margin-right: 5px;" />
          <div class="similarity-value">{{ formData.similarity }}</div>
        </div>
      </el-form-item>

      <el-form-item label="配置名">
        <el-input v-model="formData.configName" placeholder="请输入配置名" />
      </el-form-item>
    </el-form>
    <el-button style="width: 100%; " type="primary" size="small" @click="handleGenerateCode" :loading="generating">
      生成代码
    </el-button>
    <!-- 显示生成的代码区域 -->
    <!-- <div style="position: relative;flex:1;overflow:auto;margin: 5px 0;">
      <el-button v-if="generatedCode" style="position: absolute; top: 5px; right: 5px; z-index: 10;" size="small"
        @click="handleCopyCode" :icon="copied ? Check : DocumentCopy">
        {{ copied ? '已复制' : '复制' }}
      </el-button>
      <vue-json-viewer style="text-align: left;height:100%;overflow: hidden;" :value="generatedCode"
        :expanded="false" :preview-mode="true" boxed :copyable="false" show-double-quotes
        :show-array-index="false" />
    </div> -->
    <vue-json-viewer style="text-align: left;flex:1;overflow:auto;margin: 5px 0;" :value="generatedCode"
        :expanded="false" :preview-mode="true" boxed :copyable show-double-quotes
        :show-array-index="false" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Check, DocumentCopy } from "@element-plus/icons-vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import VueJsonViewer from "vue-json-viewer";
import "vue-json-viewer/style.css";
const props = defineProps({
  selectedDeviations: {
    type: Array,
    default: () => [],
  },
  selectionRect: {
    type: Object,
    default: null,
  },
  transparentImageUrl: {
    type: String,
    default: null,
  },
  currentImageUrl: {
    type: String,
    default: null,
  },
});

const emit = defineEmits(['start-code-generator-selection', 'stop-code-generator-selection']);

const codeGeneratorSelectionEnabled = ref(false); // false | 'searchArea' | 'clickOffsetArea' | 'clickArea'
const generating = ref(false);
const generatedCode = ref(null); // 改为对象类型，用于 vue-json-viewer
const imageSourceType = ref("current"); // 'current' | 'transparent'，默认选择当前大图
const copied = ref(false); // 复制状态

// 检查是否有左侧圈选范围
const hasSelectionRect = computed(() => {
  return props.selectionRect && props.selectionRect.w && props.selectionRect.h;
});

const formData = ref({
  resourcePath: "",
  configPath: "",
  imageName: "",
  colorDeviation: "",
  searchArea: "",
  clickOffsetArea: "",
  clickArea: "",
  similarity: 0.8,
  configName: "",
});

// 格式化相似度显示
const formatSimilarity = (val) => {
  return val.toFixed(1);
};

// 选择资源存放路径
const handleSelectResourcePath = async () => {
  try {
    const result = await ipc.invoke(ipcApiRoute.openDirectoryDialog, {
      title: "选择资源存放路径",
      defaultPath: formData.value.resourcePath || "",
    });

    if (result && result.success && result.filePath) {
      formData.value.resourcePath = result.filePath;
      // 保存路径配置
      await savePathsToDB();
      ElMessage.success("路径选择成功");
    }
  } catch (error) {
    console.error("选择资源路径失败:", error);
    ElMessage.error(`选择资源路径失败: ${error.message || "未知错误"}`);
  }
};

// 选择配置文件
const handleSelectConfigPath = async () => {
  try {
    const result = await ipc.invoke(ipcApiRoute.openFileDialog, {
      title: "选择配置文件",
      defaultPath: formData.value.configPath || "",
      filters: [
        { name: "配置文件", extensions: ["json", "yaml", "yml", "conf", "config"] },
        { name: "所有文件", extensions: ["*"] },
      ],
    });

    if (result && result.success && result.filePath) {
      formData.value.configPath = result.filePath;
      // 保存路径配置
      await savePathsToDB();
      ElMessage.success("配置文件选择成功");
    }
  } catch (error) {
    console.error("选择配置文件失败:", error);
    ElMessage.error(`选择配置文件失败: ${error.message || "未知错误"}`);
  }
};

// 获取偏色
const handleGetDeviation = () => {
  if (!props.selectedDeviations || props.selectedDeviations.length === 0) {
    ElMessage.warning(`请先在"偏色计算"标签页中选择偏色`);
    return;
  }

  // 将选中的偏色用 | 连接
  const deviationStr = props.selectedDeviations.join("|");
  formData.value.colorDeviation = deviationStr;
  ElMessage.success(`已获取 ${props.selectedDeviations.length} 个偏色`);
};

// 切换代码生成器圈选模式
const toggleCodeGeneratorSelection = (type) => {
  // 如果是偏移点击区域，需要先检查是否有左侧圈选范围
  if (type === 'clickOffsetArea' && !hasSelectionRect.value) {
    ElMessage.warning("请先在左侧进行圈选，才能使用偏移点击区域功能");
    return;
  }

  if (codeGeneratorSelectionEnabled.value === type) {
    // 取消当前圈选模式
    codeGeneratorSelectionEnabled.value = false;
    emit('stop-code-generator-selection');
    ElMessage.info("已取消圈选模式");
  } else {
    // 启动新的圈选模式
    codeGeneratorSelectionEnabled.value = type;
    emit('start-code-generator-selection', type);
    ElMessage.info("请在图片上进行圈选");
  }
};

// 接收圈选结果（由父组件调用）
const setSearchAreaFromSelection = (rect) => {
  if (rect && rect.w && rect.h) {
    const { x, y, w, h } = rect;

    // 根据当前圈选类型设置对应的输入框
    if (codeGeneratorSelectionEnabled.value === 'searchArea') {
      const areaStr = `${x},${y},${w},${h}`;
      formData.value.searchArea = areaStr;
      ElMessage.success("已获取查找区域范围");
    } else if (codeGeneratorSelectionEnabled.value === 'clickArea') {
      const areaStr = `${x},${y},${w},${h}`;
      formData.value.clickArea = areaStr;
      ElMessage.success("已获取点击区域范围");
    } else if (codeGeneratorSelectionEnabled.value === 'clickOffsetArea') {
      // 偏移点击区域需要基于左侧圈选范围计算偏移值
      if (!props.selectionRect || !props.selectionRect.w || !props.selectionRect.h) {
        ElMessage.warning("请先在左侧进行圈选，然后再圈选偏移点击区域");
        // 不取消圈选模式，让用户可以继续操作
        return;
      }

      // 计算偏移值：偏移点击区域的坐标 - 左侧圈选范围的坐标
      const offsetX = x - props.selectionRect.x;
      const offsetY = y - props.selectionRect.y;
      const areaStr = `${offsetX},${offsetY},${w},${h}`;
      formData.value.clickOffsetArea = areaStr;
      ElMessage.success("已获取偏移点击区域范围（已计算偏移值）");
    }

    // 自动取消圈选模式
    codeGeneratorSelectionEnabled.value = false;
    emit('stop-code-generator-selection');
  }
};

// 解析区域字符串 (格式: "x,y,w,h")
const parseAreaString = (areaStr) => {
  if (!areaStr || !areaStr.trim()) {
    return null;
  }
  const parts = areaStr.split(',').map(s => parseInt(s.trim()));
  if (parts.length === 4 && parts.every(p => !isNaN(p))) {
    return parts;
  }
  return null;
};

// 解析查找区域字符串为对象格式
const parseSearchAreaString = (areaStr) => {
  if (!areaStr || !areaStr.trim()) {
    return null;
  }
  const parts = areaStr.split(',').map(s => parseInt(s.trim()));
  if (parts.length === 4 && parts.every(p => !isNaN(p))) {
    return {
      x: parts[0],
      y: parts[1],
      w: parts[2],
      h: parts[3],
    };
  }
  return null;
};

// 生成代码
const handleGenerateCode = async () => {
  try {
    generating.value = true;

    // 验证必填项
    if (!formData.value.resourcePath) {
      ElMessage.warning("请选择资源存放路径");
      generating.value = false;
      return;
    }

    if (!formData.value.configPath) {
      ElMessage.warning("请选择配置文件");
      generating.value = false;
      return;
    }

    if (!formData.value.imageName) {
      ElMessage.warning("请输入图片名称");
      generating.value = false;
      return;
    }

    // 根据选择的图片类型获取图片 URL
    let imageUrl = null;
    if (imageSourceType.value === "current") {
      if (!props.currentImageUrl) {
        ElMessage.warning("请先载入当前大图");
        generating.value = false;
        return;
      }
      imageUrl = props.currentImageUrl;
    } else {
      if (!props.transparentImageUrl) {
        ElMessage.warning("请先制作透明图");
        generating.value = false;
        return;
      }
      imageUrl = props.transparentImageUrl;
    }

    // 保存图片到资源存放路径
    // 清理图片名称中的换行符、反斜杠和多余空白
    const cleanImageName = formData.value.imageName.replace(/[\r\n\t]/g, '').replace(/[\\/]/g, '').trim();
    const imageFileName = cleanImageName.endsWith('.png')
      ? cleanImageName
      : `${cleanImageName}.png`;
    const imagePath = `${formData.value.resourcePath}/${imageFileName}`;

    // 处理图片数据：如果是 base64 格式，直接提取；否则转换为 base64
    let base64Data = null;
    if (imageUrl.startsWith("data:")) {
      // 从 base64 URL 中提取 base64 字符串
      if (imageUrl.includes(',')) {
        base64Data = imageUrl.split(',')[1];
      } else {
        base64Data = imageUrl.replace(/^data:image\/\w+;base64,/, "");
      }
    } else {
      // 如果不是 base64 格式（如 blob URL 或文件 URL），需要转换为 base64
      try {
        // 创建一个图片对象来加载图片
        const img = new Image();
        img.crossOrigin = "anonymous";

        // 等待图片加载完成
        await new Promise((resolve, reject) => {
          img.onload = () => {
            try {
              // 创建 canvas 来转换图片
              const canvas = document.createElement("canvas");
              const ctx = canvas.getContext("2d");
              canvas.width = img.naturalWidth;
              canvas.height = img.naturalHeight;
              ctx.drawImage(img, 0, 0);

              // 转换为 base64
              const base64DataUrl = canvas.toDataURL("image/png");
              if (base64DataUrl.includes(',')) {
                base64Data = base64DataUrl.split(',')[1];
              } else {
                base64Data = base64DataUrl.replace(/^data:image\/\w+;base64,/, "");
              }
              resolve();
            } catch (error) {
              reject(error);
            }
          };
          img.onerror = () => reject(new Error("图片加载失败"));
          img.src = imageUrl;
        });
      } catch (error) {
        console.error("转换图片为 base64 失败:", error);
        throw new Error(`转换图片为 base64 失败: ${error.message || "未知错误"}`);
      }
    }

    if (!base64Data) {
      throw new Error("无法提取图片数据");
    }

    // 保存图片
    const saveResult = await ipc.invoke(ipcApiRoute.saveBase64Image, {
      filePath: imagePath,
      imageData: base64Data,
    });

    if (!saveResult || !saveResult.success) {
      throw new Error(saveResult?.error || "保存图片失败");
    }

    const imageTypeName = imageSourceType.value === "current" ? "当前大图" : "透明图";
    ElMessage.success(`${imageTypeName}保存成功`);

    // 生成代码
    const codeObj = {
      "方式": "找图",
    };

    if (formData.value.configName) {
      codeObj["标识"] = formData.value.configName;
    }

    // 偏移点击区域
    const clickOffsetArea = parseAreaString(formData.value.clickOffsetArea);
    if (clickOffsetArea) {
      codeObj["偏移点击区域"] = clickOffsetArea;
    }

    // 点击区域
    const clickArea = parseAreaString(formData.value.clickArea);
    if (clickArea) {
      codeObj["点击区域"] = clickArea;
    }

    // 查找区域
    const searchArea = parseSearchAreaString(formData.value.searchArea);
    if (searchArea) {
      codeObj["查找区域"] = searchArea;
    }

    // 相似度
    codeObj["相似度"] = formData.value.similarity;

    // 颜色偏色
    if (formData.value.colorDeviation && formData.value.colorDeviation.trim()) {
      const deviations = formData.value.colorDeviation.split('|').map(d => d.trim()).filter(d => d);
      if (deviations.length > 0) {
        codeObj["颜色偏色"] = deviations;
      }
    }

    // 图片路径
    // 需要根据配置文件路径和资源存放路径计算相对路径
    const path = require('path');
    const configDir = path.dirname(formData.value.configPath);
    const resourcePath = formData.value.resourcePath;

    // 计算相对路径
    let relativePath = path.relative(configDir, resourcePath);
    // Windows 路径分隔符转换为正斜杠，并去掉所有换行符和多余空白
    relativePath = relativePath.replace(/\\/g, '/').replace(/[\r\n\t]/g, '').trim();

    // 拼接图片文件名，确保最终路径字符串没有换行符和反斜杠
    let finalPathString = '';
    if (relativePath && relativePath !== '.') {
      // 如果相对路径不为空且不是当前目录，拼接路径和文件名
      const fullRelativePath = relativePath.endsWith('/')
        ? `${relativePath}${imageFileName}`
        : `${relativePath}/${imageFileName}`;
      // 清理：去掉换行符、将反斜杠转换为正斜杠
      let cleanPath = fullRelativePath.replace(/[\r\n\t]/g, '').replace(/\\/g, '/').trim();
      // 再次确保没有反斜杠（处理可能遗漏的情况）
      cleanPath = cleanPath.replace(/\\/g, '/');
      finalPathString = `os.path.join(os.path.dirname(__file__), "${cleanPath}")`;
    } else {
      // 如果资源路径就是配置文件目录，直接使用图片文件名
      // 确保图片文件名也没有反斜杠
      let cleanImageFileName = imageFileName.replace(/\\/g, '/');
      // 再次确保没有反斜杠
      cleanImageFileName = cleanImageFileName.replace(/\\/g, '/');
      finalPathString = `os.path.join(os.path.dirname(__file__), "${cleanImageFileName}")`;
    }
    // 最终确保路径字符串没有换行符和反斜杠（多次替换确保彻底清理）
    let finalPath = finalPathString.replace(/[\r\n\t]/g, '').replace(/\\/g, '/');
    // 再次替换，确保没有遗漏
    finalPath = finalPath.replace(/\\/g, '/');
    codeObj["图片路径"] = finalPath;

    // 直接使用对象，vue-json-viewer 会自动格式化显示
    generatedCode.value = codeObj;
    ElMessage.success("代码生成成功");
  } catch (error) {
    console.error("生成代码失败:", error);
    ElMessage.error(`生成代码失败: ${error.message || "未知错误"}`);
  } finally {
    generating.value = false;
  }
};


// 保存路径配置到数据库
const savePathsToDB = async () => {
  try {
    await ipc.invoke(ipcApiRoute.savePaths, {
      resourcePath: formData.value.resourcePath,
      configPath: formData.value.configPath,
    });
  } catch (error) {
    console.error("保存路径配置失败:", error);
    // 不显示错误提示，避免干扰用户操作
  }
};

// 从数据库加载路径配置
const loadPathsFromDB = async () => {
  try {
    const result = await ipc.invoke(ipcApiRoute.getPaths);
    if (result && result.success && result.data) {
      if (result.data.resourcePath) {
        formData.value.resourcePath = result.data.resourcePath;
      }
      if (result.data.configPath) {
        formData.value.configPath = result.data.configPath;
      }
    }
  } catch (error) {
    console.error("加载路径配置失败:", error);
    // 不显示错误提示，避免干扰用户操作
  }
};

// 复制代码到剪贴板
const handleCopyCode = async () => {
  if (!generatedCode.value) {
    ElMessage.warning("没有可复制的代码");
    return;
  }

  try {
    // 深拷贝代码对象
    let codeToCopy = JSON.parse(JSON.stringify(generatedCode.value));
    
    // 处理图片路径，确保没有换行符和反斜杠
    if (codeToCopy["图片路径"]) {
      // 去掉所有换行符、回车符、制表符，将反斜杠转换为正斜杠
      let cleanPath = codeToCopy["图片路径"]
        .replace(/[\r\n\t]/g, '')  // 去掉换行符、回车符、制表符
        .replace(/\\/g, '/')       // 将反斜杠转换为正斜杠
        .trim();                    // 去掉首尾空白
      
      // 再次确保没有反斜杠（多次替换确保彻底清理）
      cleanPath = cleanPath.replace(/\\/g, '/');
      
      codeToCopy["图片路径"] = cleanPath;
    }

    // 转换为 JSON 字符串，使用 2 空格缩进
    let jsonString = JSON.stringify(codeToCopy, null, 2);
    
    // 处理 JSON 字符串，将图片路径行中的转义反斜杠 \\ 替换为正斜杠 /
    // 按行处理，找到包含 "图片路径" 的行
    const lines = jsonString.split('\n');
    const processedLines = lines.map(line => {
      if (line.includes('"图片路径"')) {
        // 在这一行中，将 \\ 替换为 /（但保留 \" 中的反斜杠）
        // 实际上，由于我们在对象中已经清理了反斜杠，这里主要是处理 JSON 转义
        return line.replace(/\\\\/g, '/');
      }
      return line;
    });
    jsonString = processedLines.join('\n');
    
    // 复制到剪贴板
    await navigator.clipboard.writeText(jsonString);
    
    copied.value = true;
    ElMessage.success("代码已复制到剪贴板");
    
    // 2秒后重置复制状态
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (error) {
    console.error("复制代码失败:", error);
    ElMessage.error(`复制代码失败: ${error.message || "未知错误"}`);
  }
};

// 组件挂载时加载保存的路径
onMounted(() => {
  loadPathsFromDB();
});

// 暴露表单数据供外部访问
defineExpose({
  getFormData: () => formData.value,
  resetForm: () => {
    formData.value = {
      resourcePath: "",
      configPath: "",
      imageName: "",
      colorDeviation: "",
      searchArea: "",
      clickOffsetArea: "",
      clickArea: "",
      similarity: 0.8,
      configName: "",
    };
    generatedCode.value = null;
  },
  setSearchAreaFromSelection,
  getCodeGeneratorSelectionEnabled: () => codeGeneratorSelectionEnabled.value,
});
</script>

<style lang="less">
// vue-json-viewer 样式覆盖
.code-generator-tab .jv-container {

  .jv-light {
    // background: #1a1a2e;
  }
  &.boxed:hover{
    box-shadow: none;
    border: 1px solid #dcdfe6;
  }

  .jv-code {
    padding: 5px !important;
  }
}



.code-generator-tab {
  padding: 2px;
  height: 590px;
  display: flex;
  flex-direction: column;
}

.similarity-value {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}



.el-form-item {
  margin-bottom: 5px;
}
</style>
