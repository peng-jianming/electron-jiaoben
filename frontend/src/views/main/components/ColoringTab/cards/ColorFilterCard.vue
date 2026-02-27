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

<style scoped lang="less">
@primary: #6366f1;
@bg-card: #ffffff;
@text-primary: #1e293b;
@text-secondary: #64748b;
@border: #e2e8f0;
@shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);

.card {
  background: @bg-card;
  border-radius: 10px;
  border: 1px solid @border;
  overflow: hidden;
  box-shadow: @shadow-sm;
  transition: border-color 0.2s ease;
}

.card:hover {
  border-color: #cbd5e1;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.04) 0%, rgba(139, 92, 246, 0.08) 100%);
  border-bottom: 1px solid @border;
}

.card-header h2 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  flex: 1;
  color: @text-primary;
}

.card-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.filter-icon {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  color: white;
}

.card-body {
  padding: 12px 14px;
}

.filter-group {
  margin-bottom: 14px;
}

.filter-group:last-child {
  margin-bottom: 0;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.group-label {
  font-size: 12px;
  font-weight: 500;
  color: @text-secondary;
}

.color-inputs {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.color-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-preview {
  width: 26px;
  height: 26px;
  border-radius: 5px;
  border: 1.5px solid @border;
  flex-shrink: 0;
}

.color-input-row :deep(.el-input) {
  flex: 1;
}
</style>

