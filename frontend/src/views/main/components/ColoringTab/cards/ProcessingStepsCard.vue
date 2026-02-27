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

<style scoped lang="less">
@primary: #6366f1;
@success: #10b981;
@bg-card: #ffffff;
@text-primary: #1e293b;
@text-secondary: #64748b;
@text-muted: #94a3b8;
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
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.04) 0%, rgba(236, 72, 153, 0.08) 100%);
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

.steps-icon {
  background: linear-gradient(135deg, #ec4899, #f472b6);
  color: white;
}

.card-body {
  padding: 12px 14px;
}

.card-footer {
  padding: 10px 14px;
  background: #fafbfc;
  border-top: 1px solid @border;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.footer-actions {
  display: flex;
  gap: 8px;
}

.steps-card {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 150px);
}

.step-count {
  font-size: 11px;
  color: @primary;
  background: rgba(99, 102, 241, 0.08);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.steps-body {
  flex: 1;
  overflow-y: auto;
  min-height: 150px;
}

.empty-steps {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  color: @text-muted;
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 10px;
  opacity: 0.3;
}

.empty-steps p {
  margin: 0;
  text-align: center;
  font-size: 13px;
}

.empty-steps .hint {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.6;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid transparent;
  cursor: grab;
  transition: all 0.15s ease;
}

.step-item:hover {
  background: #f1f5f9;
  border-color: @border;
}

.step-item.dragging {
  opacity: 0.5;
  border-color: @primary;
  background: rgba(99, 102, 241, 0.04);
}

.step-item.completed {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.04);
}

.step-drag-handle {
  color: @text-muted;
  cursor: grab;
  padding: 2px;
  font-size: 14px;
}

.step-drag-handle:active {
  cursor: grabbing;
}

.step-index {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: @primary;
  color: white;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
}

.step-icon {
  width: 24px;
  height: 24px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
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
  font-size: 13px;
  font-weight: 500;
  color: @text-primary;
  margin-bottom: 1px;
}

.step-params {
  font-size: 11px;
  color: @text-muted;
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
  color: @success;
  font-size: 16px;
}

.step-animation-btn {
  opacity: 1 !important;
  transition: transform 0.15s ease;
}

.step-animation-btn:hover {
  transform: scale(1.05);
}

.step-delete {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.step-item:hover .step-delete {
  opacity: 1;
}

.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.25s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-leave-active {
  position: absolute;
}
</style>

