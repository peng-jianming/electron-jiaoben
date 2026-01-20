<template>
  <section class="card steps-card">
    <div class="card-header">
      <div class="card-icon steps-icon">
        <el-icon><List /></el-icon>
      </div>
      <h2>处理步骤</h2>
      <span class="step-count">{{ processingSteps.length }} 个步骤</span>
    </div>
    
    <div class="card-body steps-body">
      <div v-if="processingSteps.length === 0" class="empty-steps">
        <el-icon class="empty-icon"><DocumentAdd /></el-icon>
        <p>暂无处理步骤</p>
        <p class="hint">点击左侧模块的"添加步骤"按钮来添加</p>
      </div>
      
      <div v-else class="steps-list">
        <TransitionGroup name="list">
          <div
            v-for="(step, index) in processingSteps"
            :key="step.id"
            class="step-item"
            :class="{ 'dragging': dragIndex === index, 'completed': step.completed }"
            draggable="true"
            @dragstart="handleDragStart(index, $event)"
            @dragover="handleDragOver(index, $event)"
            @dragend="handleDragEnd"
            @drop="handleDrop(index, $event)"
          >
            <div class="step-drag-handle">
              <el-icon><Rank /></el-icon>
            </div>
            <div class="step-index">{{ index + 1 }}</div>
            <div class="step-icon" :class="step.type">
              <el-icon v-if="step.type === 'color_filter'"><Brush /></el-icon>
              <el-icon v-else-if="step.type === 'binary'"><MagicStick /></el-icon>
              <el-icon v-else-if="step.type === 'flood_fill'"><Aim /></el-icon>
            </div>
            <div class="step-content">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-params">{{ step.description }}</div>
            </div>
            <!-- 洪水填充的动画按钮 -->
            <el-button 
              v-if="step.type === 'flood_fill' && step.completed"
              type="success" 
              size="small"
              :icon="VideoPlay"
              circle
              @click.stop="$emit('show-flood-animation', index, step)"
              class="step-animation-btn"
              title="查看填充动画"
            />
            <div class="step-status" v-if="step.completed">
              <el-icon class="check-icon"><Check /></el-icon>
            </div>
            <el-button 
              type="danger" 
              size="small"
              :icon="Delete" 
              circle
              @click="$emit('remove-step', index)"
              class="step-delete"
            />
          </div>
        </TransitionGroup>
      </div>
    </div>
    
    <div class="card-footer" v-if="imageLoaded">
      <el-button 
        type="danger" 
        :icon="Delete"
        @click="$emit('clear-all')"
        :disabled="processing || processingSteps.length === 0"
      >
        清空列表
      </el-button>
      <div class="footer-actions">
        <el-button 
          type="success" 
          :icon="Download"
          @click="$emit('save-image')"
          :disabled="processing"
        >
          保存图片
        </el-button>
        <el-button 
          type="primary" 
          :icon="VideoPlay"
          @click="$emit('start-processing')"
          :disabled="processing"
          :loading="processing"
        >
          {{ processing ? '处理中...' : (processingSteps.length === 0 ? '显示原图' : '开始处理') }}
        </el-button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { 
  List, DocumentAdd, Rank, Check, Delete, VideoPlay,
  Brush, MagicStick, Aim, Download
} from '@element-plus/icons-vue';

const props = defineProps({
  processingSteps: Array,
  dragIndex: Number,
  imageLoaded: Boolean,
  processing: Boolean
});

const emit = defineEmits([
  'remove-step',
  'clear-all',
  'start-processing',
  'drag-start',
  'drag-over',
  'drag-end',
  'drop',
  'show-flood-animation',
  'save-image'
]);

function handleDragStart(index, event) {
  emit('drag-start', index, event);
}

function handleDragOver(index, event) {
  emit('drag-over', index, event);
}

function handleDragEnd() {
  emit('drag-end');
}

function handleDrop(index, event) {
  emit('drop', index, event);
}
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

.steps-icon {
  background: linear-gradient(135deg, #ec4899, #f472b6);
  color: white;
}

.card-body {
  padding: 20px;
}

.card-footer {
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.3);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.footer-actions {
  display: flex;
  gap: 12px;
}

.steps-card {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 150px);
}

.step-count {
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(99, 102, 241, 0.2);
  padding: 4px 10px;
  border-radius: 12px;
}

.steps-body {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
}

.empty-steps {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-steps p {
  margin: 0;
  text-align: center;
}

.empty-steps .hint {
  font-size: 12px;
  margin-top: 8px;
  opacity: 0.7;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 10px;
  border: 1px solid transparent;
  cursor: grab;
  transition: all 0.2s ease;
}

.step-item:hover {
  background: rgba(51, 65, 85, 0.5);
  border-color: var(--primary-color);
}

.step-item.dragging {
  opacity: 0.5;
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
}

.step-item.completed {
  border-color: var(--success-color);
  background: rgba(16, 185, 129, 0.1);
}

.step-drag-handle {
  color: var(--text-secondary);
  cursor: grab;
  padding: 4px;
}

.step-drag-handle:active {
  cursor: grabbing;
}

.step-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.step-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.step-icon.color_filter {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  color: white;
}

.step-icon.binary {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: white;
}

.step-icon.flood_fill {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: white;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.step-params {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-status {
  display: flex;
  align-items: center;
  justify-content: center;
}

.check-icon {
  color: var(--success-color);
  font-size: 18px;
}

.step-animation-btn {
  opacity: 1 !important;
  transition: transform 0.2s ease;
}

.step-animation-btn:hover {
  transform: scale(1.1);
}

.step-delete {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.step-item:hover .step-delete {
  opacity: 1;
}

/* 列表过渡动画 */
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.list-leave-active {
  position: absolute;
}
</style>

