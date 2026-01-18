<template>
  <div class="code-generator-tab">
    <el-form :model="formData" label-width="90px" size="small">
      <!-- 资源存放路径选择框 -->
      <el-form-item label="资源存放路径">
        <el-input
          v-model="formData.resourcePath"
          placeholder="请选择资源存放路径"
          readonly
        >
          <template #append>
            <el-button @click="handleSelectResourcePath">选择</el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 配置文件选择框 -->
      <el-form-item label="配置文件">
        <el-input
          v-model="formData.configPath"
          placeholder="请选择配置文件"
          readonly
        >
          <template #append>
            <el-button @click="handleSelectConfigPath">选择</el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 图片名输入框 -->
      <el-form-item label="图片名">
        <el-input
          v-model="formData.imageName"
          placeholder="请输入图片名称"
        />
      </el-form-item>

      <!-- 颜色偏色输入框 -->
      <el-form-item label="颜色偏色">
        <el-input
          v-model="formData.colorDeviation"
          placeholder="请输入颜色偏色，例如：D7CCC6-0E0E09"
        >
          <template #append>
            <el-button @click="handleGetDeviation">获取偏色</el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 查找区域输入框 -->
      <el-form-item label="查找区域">
        <el-input
          v-model="formData.searchArea"
          placeholder="请输入查找区域，格式：x,y,w,h"
        >
          <template #append>
            <el-button 
              :type="codeGeneratorSelectionEnabled === 'searchArea' ? 'warning' : 'primary'"
              @click="toggleCodeGeneratorSelection('searchArea')"
            >
              {{ codeGeneratorSelectionEnabled === 'searchArea' ? '取消圈选范围' : '启动圈选范围' }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 偏移点击区域输入框 -->
      <el-form-item label="偏移点击区域">
        <el-input
          v-model="formData.clickOffsetArea"
          placeholder="请输入偏移点击区域，格式：x,y,w,h"
        >
          <template #append>
            <el-button 
              :type="codeGeneratorSelectionEnabled === 'clickOffsetArea' ? 'warning' : 'primary'"
              :disabled="!hasSelectionRect"
              @click="toggleCodeGeneratorSelection('clickOffsetArea')"
            >
              {{ codeGeneratorSelectionEnabled === 'clickOffsetArea' ? '取消圈选范围' : '启动圈选范围' }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 点击区域输入框 -->
      <el-form-item label="点击区域">
        <el-input
          v-model="formData.clickArea"
          placeholder="请输入点击区域，格式：x,y,w,h"
        >
          <template #append>
            <el-button 
              :type="codeGeneratorSelectionEnabled === 'clickArea' ? 'warning' : 'primary'"
              @click="toggleCodeGeneratorSelection('clickArea')"
            >
              {{ codeGeneratorSelectionEnabled === 'clickArea' ? '取消圈选范围' : '启动圈选范围' }}
            </el-button>
          </template>
        </el-input>
      </el-form-item>

      <!-- 相似度选择框 -->
      <el-form-item label="相似度">
        <div style="display: flex; align-items: center; width: 100%">
          <el-slider
          v-model="formData.similarity"
          :min="0.1"
          :max="1"
          :step="0.1"
          :format-tooltip="formatSimilarity"
          style="flex:1; margin-right: 5px;"
        />
        <div class="similarity-value">{{ formData.similarity }}</div>
        </div>
      </el-form-item>

      <el-form-item label="配置名">
        <el-input
          v-model="formData.configName"
          placeholder="请输入配置名"
        />
      </el-form-item>
    </el-form>
    <el-button 
      style="width: 100%; margin-top: 10px;" 
      type="primary" 
      size="small"
      @click="handleGenerateCode"
      :loading="generating"
    >
      生成代码
    </el-button>
    <!-- 显示生成的代码区域 -->
    <div v-if="generatedCode" class="generated-code-section">
      <div class="code-header">
        <span>生成的代码：</span>
        <el-button 
          type="text" 
          size="small" 
          @click="handleCopyCode"
          style="padding: 0; margin-left: 10px;"
        >
          复制代码
        </el-button>
      </div>
      <pre class="code-content">{{ generatedCode }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";

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
});

const emit = defineEmits(['start-code-generator-selection', 'stop-code-generator-selection']);

const codeGeneratorSelectionEnabled = ref(false); // false | 'searchArea' | 'clickOffsetArea' | 'clickArea'
const generating = ref(false);
const generatedCode = ref("");

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

    if (!props.transparentImageUrl) {
      ElMessage.warning("请先制作透明图");
      generating.value = false;
      return;
    }

    // 保存透明图到资源存放路径
    const imageFileName = formData.value.imageName.endsWith('.png') 
      ? formData.value.imageName 
      : `${formData.value.imageName}.png`;
    const imagePath = `${formData.value.resourcePath}/${imageFileName}`;

    // 从 base64 URL 中提取 base64 字符串
    let base64Data = props.transparentImageUrl;
    if (base64Data.includes(',')) {
      base64Data = base64Data.split(',')[1];
    }

    // 保存图片
    const saveResult = await ipc.invoke(ipcApiRoute.saveBase64Image, {
      filePath: imagePath,
      imageData: base64Data,
    });

    if (!saveResult || !saveResult.success) {
      throw new Error(saveResult?.error || "保存透明图失败");
    }

    ElMessage.success("透明图保存成功");

    // 生成代码
    const codeObj = {
      "方式": "找图",
    };

    if(formData.value.configName) {
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
    // Windows 路径分隔符转换为正斜杠
    relativePath = relativePath.replace(/\\/g, '/');
    
    // 拼接图片文件名
    if (relativePath && relativePath !== '.') {
      // 如果相对路径不为空且不是当前目录，拼接路径和文件名
      const fullRelativePath = relativePath.endsWith('/') 
        ? `${relativePath}${imageFileName}`
        : `${relativePath}/${imageFileName}`;
      codeObj["图片路径"] = `os.path.join(os.path.dirname(__file__), "${fullRelativePath}")`;
    } else {
      // 如果资源路径就是配置文件目录，直接使用图片文件名
      codeObj["图片路径"] = `os.path.join(os.path.dirname(__file__), "${imageFileName}")`;
    }

    // 格式化代码为 JSON 字符串
    const formatCode = (obj) => {
      const lines = [];
      lines.push('{');
      
      const entries = Object.entries(obj);
      entries.forEach(([key, value], index) => {
        // 所有行都添加逗号，包括最后一行
        const comma = ',';
        
        if (Array.isArray(value)) {
          // 数组格式
          if (value.length === 0) {
            lines.push(`  "${key}": []${comma}`);
          } else if (value.every(v => typeof v === 'number')) {
            // 数字数组
            lines.push(`  "${key}": [${value.join(' ,')}]${comma}`);
          } else {
            // 字符串数组
            const arrStr = value.map(v => `"${v}"`).join(', ');
            lines.push(`  "${key}": [${arrStr}]${comma}`);
          }
        } else if (typeof value === 'object' && value !== null) {
          // 对象格式
          lines.push(`  "${key}": {`);
          lines.push(`    "x": ${value.x},`);
          lines.push(`    "y": ${value.y},`);
          lines.push(`    "w": ${value.w},`);
          lines.push(`    "h": ${value.h}`);
          lines.push(`  }${comma}`);
        } else if (typeof value === 'string') {
          // 字符串（可能是代码表达式）
          lines.push(`  "${key}": ${value}${comma}`);
        } else {
          // 数字或其他
          lines.push(`  "${key}": ${value}${comma}`);
        }
      });
      
      lines.push('},');
      return lines.join('\n');
    };

    generatedCode.value = formatCode(codeObj);
    ElMessage.success("代码生成成功");
  } catch (error) {
    console.error("生成代码失败:", error);
    ElMessage.error(`生成代码失败: ${error.message || "未知错误"}`);
  } finally {
    generating.value = false;
  }
};

// 复制代码
const handleCopyCode = async () => {
  if (!generatedCode.value) {
    ElMessage.warning("没有可复制的代码");
    return;
  }

  try {
    await navigator.clipboard.writeText(generatedCode.value);
    ElMessage.success("代码已复制到剪贴板");
  } catch (error) {
    console.error("复制失败:", error);
    ElMessage.error("复制失败，请手动复制");
  }
};

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
    generatedCode.value = "";
  },
  setSearchAreaFromSelection,
  getCodeGeneratorSelectionEnabled: () => codeGeneratorSelectionEnabled.value,
});
</script>

<style scoped>
.code-generator-tab {
  padding: 10px;
  height: 590px;
  overflow-y: auto;
}

.similarity-value {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}

.hint-text {
  margin-top: 5px;
  font-size: 12px;
  color: #f56c6c;
  font-style: italic;
}

.generated-code-section {
  margin-top: 15px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-weight: 500;
  color: #303133;
}

.code-content {
  margin: 0;
  padding: 10px;
  background-color: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}
</style>

