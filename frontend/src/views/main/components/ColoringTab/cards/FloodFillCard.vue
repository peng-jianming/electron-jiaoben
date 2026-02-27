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

<style scoped lang="less">
@success: #10b981;
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
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.04) 0%, rgba(16, 185, 129, 0.08) 100%);
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

.flood-icon {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: white;
}

.card-body {
  padding: 12px 14px;
}

.flood-info {
  margin-bottom: 0;
}

.point-display {
  display: flex;
  align-items: center;
}

.point-display :deep(.el-tag) {
  padding: 6px 12px;
  font-size: 12px;
}
</style>

