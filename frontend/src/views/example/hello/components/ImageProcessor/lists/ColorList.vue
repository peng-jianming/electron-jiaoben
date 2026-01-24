<template>
  <div>
    <el-table :data="colors" height="205" border size="small" empty-text="等待选取颜色">
      <el-table-column type="index" label="#"> </el-table-column>
      <el-table-column label="个数" width="80">
        <template #default="scope">
          {{ scope.row.count || 1 }}
        </template>
      </el-table-column>
      <el-table-column prop="hex" label="hex" width="80">
        <template #default="scope">
          <div :style="{
            'background-color': scope.row.hex,
            color: isLightColor(scope.row.hex) ? '#000000' : '#ffffff',
          }">
            {{ scope.row.hex }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="70">
        <template #default="scope">
          <el-button type="text" size="small" @click="$emit('remove-color', scope.$index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="padding: 0 5px;">
      <el-button type="danger" size="small" @click="$emit('clear-all-colors')" class="clear-all-btn" style="margin-top: 5px;">
        清空全部
      </el-button>
      <el-button type="primary" size="small" class="clear-all-btn" @click="$emit('calculate-deviation')" :disabled="isPreviewEnabled">
        计算偏色
      </el-button>
      <div style="display: flex; align-items: center; margin-top: 5px; gap: 10px;">
        <el-checkbox v-model="isPreviewEnabled" :disabled="!colors.length" @change="handlePreviewToggle">偏色</el-checkbox>
        <el-slider 
          v-model="deviationValue" 
          :min="0" 
          :max="100" 
          :disabled="!isPreviewEnabled"
          style="flex: 1;"
          @input="handleDeviationChange"
        />
      </div>
      <el-button 
        type="success" 
        size="small" 
        class="clear-all-btn" 
        @click="handleAddToDeviationList"
        :disabled="!isPreviewEnabled || colors.length === 0"
        style="margin-top: 5px;"
      >
        添加进偏色列表
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  colors: {
    type: Array,
    default: () => [],
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

const emit = defineEmits(["remove-color", "calculate-deviation", "clear-all-colors", "add-colors", "preview-toggle", "deviation-change", "add-to-deviation-list"]);

const isPreviewEnabled = ref(false);
const deviationValue = ref(0);

// 判断颜色是否偏白（根据亮度计算）
const isLightColor = (hex) => {
  // 移除 # 号
  hex = hex.replace("#", "");

  // 如果是3位hex，转换为6位
  if (hex.length === 3) {
    hex = hex
      .split("")
      .map((char) => char + char)
      .join("");
  }

  // 转换为 RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // 计算相对亮度（W3C 标准公式）
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;

  // 如果亮度大于 186（约 73%），则认为偏白，使用黑色字体
  return luminance > 186;
};

// 处理预览开关
const handlePreviewToggle = (value) => {
  emit("preview-toggle", value);
};

// 处理偏差值变化
const handleDeviationChange = (value) => {
  emit("deviation-change", value);
};

// 添加进偏色列表
const handleAddToDeviationList = () => {
  if (props.colors.length === 0) {
    ElMessage.warning("请先选取颜色");
    return;
  }
  emit("add-to-deviation-list", {
    baseColor: props.colors[0],
    deviation: deviationValue.value
  });
};
</script>

<style scoped>
.clear-all-btn {
  width: 100%;
  margin-top: 5px;
}
.el-button+.el-button {
  margin-left: 0;
}
</style>

