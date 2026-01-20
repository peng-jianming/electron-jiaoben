<template>
  <section class="card filter-card">
    <div class="card-header">
      <div class="card-icon filter-icon">
        <el-icon><Brush /></el-icon>
      </div>
      <h2>颜色过滤</h2>
      <el-button 
        type="primary" 
        size="small" 
        :icon="Plus"
        @click="$emit('add-step')"
        :disabled="!imageLoaded"
      >
        添加步骤
      </el-button>
    </div>
    
    <div class="card-body">
      <!-- 保留颜色 -->
      <div class="filter-group">
        <div class="group-header">
          <span class="group-label">保留颜色</span>
          <el-button 
            type="primary" 
            size="small" 
            :icon="Plus"
            circle
            @click="$emit('add-keep-color')"
          />
        </div>
        <div class="color-inputs">
          <div 
            v-for="(item, index) in keepColors"
            :key="'keep-' + index"
            class="color-input-row"
          >
            <div 
              class="color-preview" 
              :style="{ backgroundColor: getColorPreview(keepColors[index]) }"
            ></div>
            <el-input
              :model-value="keepColors[index]"
              @update:model-value="$emit('update-keep-color', index, $event)"
              placeholder="格式: RRGGBB-容差"
            />
            <el-button 
              type="danger" 
              size="small"
              :icon="Delete" 
              circle
              @click="$emit('remove-keep-color', index)"
            />
          </div>
        </div>
      </div>

      <!-- 过滤颜色 -->
      <div class="filter-group">
        <div class="group-header">
          <span class="group-label">过滤颜色</span>
          <el-button 
            type="primary" 
            size="small" 
            :icon="Plus"
            circle
            @click="$emit('add-filter-color')"
          />
        </div>
        <div class="color-inputs">
          <div 
            v-for="(item, index) in filterColors"
            :key="'filter-' + index"
            class="color-input-row"
          >
            <div 
              class="color-preview" 
              :style="{ backgroundColor: getColorPreview(filterColors[index]) }"
            ></div>
            <el-input
              :model-value="filterColors[index]"
              @update:model-value="$emit('update-filter-color', index, $event)"
              placeholder="格式: RRGGBB-容差"
            />
            <el-button 
              type="danger" 
              size="small"
              :icon="Delete" 
              circle
              @click="$emit('remove-filter-color', index)"
            />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Brush, Plus, Delete } from '@element-plus/icons-vue';

defineProps({
  imageLoaded: Boolean,
  keepColors: Array,
  filterColors: Array,
  getColorPreview: Function
});

defineEmits([
  'add-step',
  'add-keep-color',
  'remove-keep-color',
  'update-keep-color',
  'add-filter-color',
  'remove-filter-color',
  'update-filter-color'
]);
</script>

<style scoped>
.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: var(--shadow-lg);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.3);
  border-bottom: 1px solid var(--border-color);
}

.card-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}

.card-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.filter-icon {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  color: white;
}

.card-body {
  padding: 20px;
}

.filter-group {
  margin-bottom: 20px;
}

.filter-group:last-child {
  margin-bottom: 0;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.group-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.color-inputs {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.color-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-preview {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid var(--border-color);
  flex-shrink: 0;
}

.color-input-row :deep(.el-input) {
  flex: 1;
}

:deep(.el-input__wrapper) {
  background: rgba(51, 65, 85, 0.5);
  border: 1px solid var(--border-color);
  box-shadow: none !important;
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--primary-color);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
}

:deep(.el-input__inner) {
  color: var(--text-primary);
}
</style>

