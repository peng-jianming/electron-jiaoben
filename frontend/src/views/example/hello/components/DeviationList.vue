<template>
  <div class="deviation-list">
    <div class="deviation-header">
      偏色列表
    </div>
    <div>
      <el-scrollbar height="162px" style="padding: 5px">
        <el-checkbox-group v-model="selectedDeviations" size="small"
          style="display: flex; flex-direction: column; gap: 5px">
          <el-checkbox v-for="(item, index) in deviationColors" :key="index" :label="item"
            border></el-checkbox>
        </el-checkbox-group>
      </el-scrollbar>
    </div>
    <div style="padding: 0 5px;">
      <el-button type="primary" size="small" class="clear-all-btn" @click="$emit('clear-deviations')">
        清空偏色
      </el-button>
      <el-button type="primary" size="small" class="clear-all-btn" @click="$emit('rerender')">
        重新渲染
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  deviationColors: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:modelValue", "clear-deviations", "rerender"]);

const selectedDeviations = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});
</script>

<style scoped>
.deviation-list {
  color: #909399;
  border: 1px solid #dcdfe6;
  margin-left: 5px;
  width: 170px;
}

.deviation-header {
  font-size: 14px;
  padding: 5px;
  border-bottom: 1px solid #dcdfe6;
}

.clear-all-btn {
  width: 100%;
  margin-top: 5px;
}

.el-checkbox {
  margin-right: 0;
}
</style>

