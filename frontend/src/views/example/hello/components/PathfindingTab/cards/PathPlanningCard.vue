<template>
  <section class="card pathfinding-card">
    <div class="card-header">
      <div class="card-icon route-icon">
        <el-icon><Guide /></el-icon>
      </div>
      <h2>路径规划</h2>
    </div>
    
    <div class="card-body">
      <div class="pathfinding-controls">
        <h3 class="section-title">
          <el-icon><MapLocation /></el-icon>
          地图与路线规划
        </h3>
        <p class="section-desc">载入二值化地图，设置起点和终点，然后进行路径规划</p>
        
        <!-- 载入地图 -->
        <div class="control-row">
          <el-button 
            type="primary" 
            :icon="Upload"
            @click="$emit('load-map')"
            class="control-btn"
          >
            载入地图
          </el-button>
          <span class="file-name" v-if="mapLoaded">{{ mapFileName }}</span>
        </div>

        <!-- 起点终点设置 -->
        <div class="points-row" v-if="mapLoaded">
          <div class="point-input">
            <span class="point-label start-label">起点:</span>
            <el-input-number 
              :model-value="startPoint.x"
              @update:model-value="$emit('update-start-point', { ...startPoint, x: $event })"
              :min="0" 
              size="small" 
              placeholder="X"
              controls-position="right"
            />
            <el-input-number 
              :model-value="startPoint.y"
              @update:model-value="$emit('update-start-point', { ...startPoint, y: $event })"
              :min="0" 
              size="small" 
              placeholder="Y"
              controls-position="right"
            />
            <el-button 
              type="success" 
              size="small"
              :icon="Aim"
              @click="$emit('set-start-point')"
              :disabled="!mapWindowOpen"
            >
              点击选取
            </el-button>
          </div>
          <div class="point-input">
            <span class="point-label end-label">终点:</span>
            <el-input-number 
              :model-value="endPoint.x"
              @update:model-value="$emit('update-end-point', { ...endPoint, x: $event })"
              :min="0" 
              size="small" 
              placeholder="X"
              controls-position="right"
            />
            <el-input-number 
              :model-value="endPoint.y"
              @update:model-value="$emit('update-end-point', { ...endPoint, y: $event })"
              :min="0" 
              size="small" 
              placeholder="Y"
              controls-position="right"
            />
            <el-button 
              type="danger" 
              size="small"
              :icon="Aim"
              @click="$emit('set-end-point')"
              :disabled="!mapWindowOpen"
            >
              点击选取
            </el-button>
          </div>
        </div>

        <!-- 路径规划按钮 -->
        <div class="button-group" v-if="mapLoaded">
          <el-button 
            type="warning" 
            :icon="Promotion"
            @click="$emit('plan-route')"
            :disabled="!hasValidPoints"
            :loading="planning"
            class="control-btn"
          >
            {{ planning ? '规划中...' : '进行路线规划' }}
          </el-button>
          <el-button 
            v-if="hasPath"
            type="info" 
            :icon="Delete"
            @click="$emit('clear-path')"
            class="control-btn"
          >
            清除路径
          </el-button>
        </div>

        <!-- 状态信息 -->
        <div class="status-info" v-if="mapLoaded">
          <div class="status-item">
            <span class="status-label">地图尺寸:</span>
            <el-tag type="info" size="small">{{ mapSize.width }} × {{ mapSize.height }}</el-tag>
          </div>
          <div class="status-item" v-if="hasPath">
            <span class="status-label">路径长度:</span>
            <el-tag type="success" size="small">{{ pathLength }} 步</el-tag>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Guide, MapLocation, Upload, Aim, Promotion, Delete } from '@element-plus/icons-vue';

defineProps({
  mapLoaded: Boolean,
  mapWindowOpen: Boolean,
  mapFileName: String,
  mapSize: Object,
  startPoint: Object,
  endPoint: Object,
  planning: Boolean,
  hasPath: Boolean,
  pathLength: Number,
  hasValidPoints: Boolean
});

defineEmits([
  'load-map',
  'set-start-point',
  'set-end-point',
  'update-start-point',
  'update-end-point',
  'plan-route',
  'clear-path'
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

.pathfinding-card {
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(236, 72, 153, 0.05) 100%);
}

.route-icon {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: white;
}

.card-body {
  padding: 24px;
}

.pathfinding-controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.pathfinding-controls .section-title .el-icon {
  color: #f59e0b;
}

.section-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

.button-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.control-btn {
  padding: 12px 24px !important;
  font-size: 15px !important;
  font-weight: 500;
  border-radius: 10px !important;
  transition: all 0.3s ease;
}

.control-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-name {
  font-size: 14px;
  color: var(--text-secondary);
  background: rgba(51, 65, 85, 0.4);
  padding: 6px 12px;
  border-radius: 6px;
}

.points-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.point-input {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.point-label {
  font-size: 14px;
  font-weight: 600;
  min-width: 50px;
}

.start-label {
  color: #10b981;
}

.end-label {
  color: #ef4444;
}

.point-input :deep(.el-input-number) {
  width: 100px;
}

.point-input :deep(.el-input-number .el-input__inner) {
  background: rgba(51, 65, 85, 0.4);
  border-color: var(--border-color);
  color: var(--text-primary);
}

.status-info {
  display: flex;
  gap: 24px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.4);
  border-radius: 10px;
  border: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: var(--text-secondary);
}
</style>

