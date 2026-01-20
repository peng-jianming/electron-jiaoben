<template>
  <div>
    <el-table :data="colors" height="205" border size="small" empty-text="等待选取颜色">
      <el-table-column type="index" label="#"> </el-table-column>
      <el-table-column label="坐标" width="80">
        <template #default="scope">
          {{ scope.row.x }}, {{ scope.row.y }}
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
      <el-button type="primary" size="small" class="clear-all-btn" @click="$emit('calculate-deviation')">
        计算偏色
      </el-button>
      <el-button type="danger" size="small" @click="$emit('clear-all-colors')" class="clear-all-btn">
        清空全部
      </el-button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  colors: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["remove-color", "calculate-deviation", "clear-all-colors"]);

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

