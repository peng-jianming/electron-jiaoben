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
      <el-button type="primary" size="small" class="clear-all-btn" @click="$emit('calculate-deviation')">
        计算偏色
      </el-button>
      <el-button type="primary" size="small" class="clear-all-btn" @click="handleStatisticsColors">
        统计颜色
      </el-button>
      <el-button type="danger" size="small" @click="$emit('clear-all-colors')" class="clear-all-btn">
        清空全部
      </el-button>
    </div>
  </div>
</template>

<script setup>
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

const emit = defineEmits(["remove-color", "calculate-deviation", "clear-all-colors", "add-colors"]);

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

// 统计颜色
const handleStatisticsColors = () => {
  if (!props.currentImage || !props.currentImage.url) {
    ElMessage.warning("请先载入图片");
    return;
  }

  if (!props.selectionRect || !props.selectionRect.w || !props.selectionRect.h) {
    ElMessage.warning("请先圈选区域");
    return;
  }

  // 创建图片对象
  const img = new Image();
  img.crossOrigin = "anonymous";
  
  img.onload = () => {
    try {
      // 创建 canvas 用于处理
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");

      // 确定处理区域
      const startX = Math.max(0, Math.min(props.selectionRect.x, img.width - 1));
      const startY = Math.max(0, Math.min(props.selectionRect.y, img.height - 1));
      const width = Math.min(props.selectionRect.w, img.width - startX);
      const height = Math.min(props.selectionRect.h, img.height - startY);

      // 设置 canvas 尺寸
      canvas.width = width;
      canvas.height = height;

      // 绘制原始图片区域到 canvas
      ctx.drawImage(img, startX, startY, width, height, 0, 0, width, height);

      // 获取像素数据
      const imageData = ctx.getImageData(0, 0, width, height);
      const data = imageData.data;

      // 统计颜色
      const colorMap = new Map(); // 使用 Map 来统计每个颜色的数量

      // 遍历每个像素
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        const a = data[i + 3];

        // 跳过完全透明的像素
        if (a === 0) {
          continue;
        }

        // 转换为 HEX
        const hex = `#${[r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("")}`.toUpperCase();
        const rgb = `rgb(${r}, ${g}, ${b})`;

        // 统计颜色数量
        if (colorMap.has(hex)) {
          colorMap.set(hex, colorMap.get(hex) + 1);
        } else {
          colorMap.set(hex, 1);
        }
      }

      // 转换为数组格式
      const colorStats = Array.from(colorMap.entries()).map(([hex, count]) => {
        const rgbMatch = hex.match(/^#([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})$/i);
        const r = parseInt(rgbMatch[1], 16);
        const g = parseInt(rgbMatch[2], 16);
        const b = parseInt(rgbMatch[3], 16);
        return {
          hex,
          rgb: `rgb(${r}, ${g}, ${b})`,
          count,
        };
      });

      if (colorStats.length === 0) {
        ElMessage.warning("圈选区域内没有有效像素");
        return;
      }

      // 按个数降序排序，取前10个
      const topColors = colorStats
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);

      // 通知父组件添加颜色
      emit("add-colors", topColors);
      ElMessage.success(`统计完成，已添加前 ${topColors.length} 个最多的颜色（共统计 ${colorStats.length} 种颜色）`);
    } catch (error) {
      console.error("统计颜色时出错:", error);
      ElMessage.error("统计颜色失败");
    }
  };

  img.onerror = () => {
    ElMessage.error("加载图片失败");
  };

  img.src = props.currentImage.url;
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

