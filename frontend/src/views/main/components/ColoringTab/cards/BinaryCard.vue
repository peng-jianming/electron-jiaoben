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

.binary-icon {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: white;
}

.card-body {
  padding: 20px;
}

.threshold-control {
  padding: 0 4px;
}

.threshold-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.threshold-label span {
  font-size: 14px;
  color: var(--text-secondary);
}

.threshold-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-light) !important;
}

.threshold-control :deep(.el-slider__runway) {
  background: var(--border-color);
}

.threshold-control :deep(.el-slider__bar) {
  background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
}

.threshold-control :deep(.el-slider__button) {
  border-color: var(--primary-color);
}
</style>

