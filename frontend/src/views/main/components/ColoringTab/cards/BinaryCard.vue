<template>
  <section class="card binary-card">
    <div class="card-header">
      <div class="card-icon binary-icon">
        <el-icon><MagicStick /></el-icon>
      </div>
      <h2>二值化处理</h2>
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
      <div class="threshold-control">
        <div class="threshold-label">
          <span>阈值</span>
          <span class="threshold-value">{{ threshold }}</span>
        </div>
        <el-slider
          :model-value="threshold"
          @update:model-value="$emit('update:threshold', $event)"
          :min="0"
          :max="255"
          :step="1"
          :marks="{ 0: '0', 127: '127', 255: '255' }"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { MagicStick, Plus } from '@element-plus/icons-vue';

defineProps({
  imageLoaded: Boolean,
  threshold: Number
});

defineEmits(['add-step', 'update:threshold']);
</script>

<style scoped lang="less">
@primary: #6366f1;
@primary-light: #818cf8;
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
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.04) 0%, rgba(245, 158, 11, 0.08) 100%);
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

.binary-icon {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: white;
}

.card-body {
  padding: 12px 14px;
}

.threshold-control {
  padding: 0;
}

.threshold-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.threshold-label span {
  font-size: 12px;
  color: @text-secondary;
}

.threshold-value {
  font-size: 18px;
  font-weight: 600;
  color: @primary !important;
}

.threshold-control :deep(.el-slider__runway) {
  background: @border;
}

.threshold-control :deep(.el-slider__bar) {
  background: linear-gradient(90deg, @primary, @primary-light);
}

.threshold-control :deep(.el-slider__button) {
  border-color: @primary;
}
</style>

