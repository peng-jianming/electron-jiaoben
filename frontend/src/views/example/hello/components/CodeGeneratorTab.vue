<template>
  <div class="code-generator-tab">
    <el-form :model="formData" label-width="120px" size="small">
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
        <el-slider
          v-model="formData.similarity"
          :min="0.1"
          :max="1"
          :step="0.1"
          :format-tooltip="formatSimilarity"
          style="width: 100%"
        />
        <div class="similarity-value">当前值: {{ formData.similarity }}</div>
      </el-form-item>
    </el-form>
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
});

const emit = defineEmits(['start-code-generator-selection', 'stop-code-generator-selection']);

const codeGeneratorSelectionEnabled = ref(false); // false | 'searchArea' | 'clickOffsetArea' | 'clickArea'

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
    };
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
</style>

