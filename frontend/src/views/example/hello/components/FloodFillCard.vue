<template>
  <section class="card flood-card">
    <div class="card-header">
      <div class="card-icon flood-icon">
        <el-icon><Aim /></el-icon>
      </div>
      <h2>洪水填充</h2>
      <el-button 
        type="primary" 
        size="small" 
        :icon="Plus"
        @click="$emit('add-step')"
        :disabled="!imageLoaded || !floodFillStartPoint"
      >
        添加步骤
      </el-button>
    </div>
    
    <div class="card-body">
      <div class="flood-info">
        <el-alert
          v-if="!floodFillStartPoint"
          type="info"
          :closable="false"
          show-icon
        >
          请在图片上点击选择填充起始位置
        </el-alert>
        <div v-else class="point-display">
          <el-tag type="success" effect="dark" size="large">
            <el-icon><Location /></el-icon>
            起始位置: ({{ floodFillStartPoint.x }}, {{ floodFillStartPoint.y }})
          </el-tag>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Aim, Plus, Location } from '@element-plus/icons-vue';

defineProps({
  imageLoaded: Boolean,
  floodFillStartPoint: Object
});

defineEmits(['add-step']);
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

.flood-icon {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: white;
}

.card-body {
  padding: 20px;
}

.flood-info {
  margin-bottom: 0;
}

.point-display {
  display: flex;
  align-items: center;
}

.point-display :deep(.el-tag) {
  padding: 8px 16px;
  font-size: 14px;
}

:deep(.el-alert) {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

:deep(.el-alert .el-alert__description) {
  color: var(--text-secondary);
}
</style>
