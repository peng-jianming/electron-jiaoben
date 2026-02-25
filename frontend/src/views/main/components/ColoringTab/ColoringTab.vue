<template>
  <div class="coloring-layout">
    <!-- 图像上传区 -->
    <ImageUploadCard
      :image-file-name="imageFileName"
      @image-select="handleImageSelect"
    />

    <!-- 管线区域 -->
    <div class="pipeline-section">
      <!-- 管线头部：标题 + 添加步骤 -->
      <div class="pipeline-toolbar">
        <div class="toolbar-left">
          <el-icon class="pipeline-icon"><List /></el-icon>
          <span class="pipeline-title">处理管线</span>
          <el-tag size="small" type="info" effect="dark">{{ pipeline.length }} 步</el-tag>
        </div>
        <el-dropdown trigger="click" @command="addStep" :disabled="!imageLoaded">
          <el-button type="primary" size="small" :icon="Plus" :disabled="!imageLoaded">
            添加步骤
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="color_filter">
                <el-icon><Brush /></el-icon> 颜色过滤
              </el-dropdown-item>
              <el-dropdown-item command="binary">
                <el-icon><MagicStick /></el-icon> 二值化
              </el-dropdown-item>
              <el-dropdown-item command="flood_fill">
                <el-icon><Aim /></el-icon> 洪水填充
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <!-- 步骤列表 -->
      <div class="pipeline-list" v-if="pipeline.length > 0">
        <TransitionGroup name="list">
          <PipelineStepCard
            v-for="(step, index) in pipeline"
            :key="step.id"
            :step="step"
            :index="index"
            :is-dragging="dragIndex === index"
            :is-selecting-point="activeFloodFillStepId === step.id"
            :get-color-preview="getColorPreview"
            @update:params="updateStepParams(step.id, $event)"
            @toggle-expand="toggleStepExpand(step.id)"
            @remove="removeStep(index)"
            @show-animation="showFloodFillAnimation(index, step)"
            @select-point="startPointSelection(step.id)"
            @drag-start="handleDragStart"
            @drag-over="handleDragOver"
            @drag-end="handleDragEnd"
            @drop="handleDrop"
          />
        </TransitionGroup>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-pipeline">
        <el-icon class="empty-icon"><DocumentAdd /></el-icon>
        <p>暂无处理步骤</p>
        <p class="hint">点击上方「添加步骤」来构建处理管线</p>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="action-bar" v-if="imageLoaded">
      <el-button
        type="danger"
        :icon="Delete"
        @click="clearAllSteps"
        :disabled="processing || pipeline.length === 0"
      >
        清空
      </el-button>
      <div class="action-right">
        <el-button
          type="success"
          :icon="Download"
          @click="handleSaveImage"
          :disabled="processing"
        >
          保存图片
        </el-button>
        <el-button
          type="primary"
          :icon="VideoPlay"
          @click="startProcessing"
          :disabled="processing"
          :loading="processing"
        >
          {{ processing ? '处理中...' : (pipeline.length === 0 ? '显示原图' : '开始处理') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import {
  List, Plus, Delete, Download, VideoPlay, DocumentAdd,
  Brush, MagicStick, Aim,
} from '@element-plus/icons-vue';
import { useColoring } from '../../composables/useColoring';
import ImageUploadCard from './cards/ImageUploadCard.vue';
import PipelineStepCard from './cards/PipelineStepCard.vue';

const {
  imageFileName,
  processing,
  imageLoaded,
  pipeline,
  dragIndex,
  activeFloodFillStepId,

  getColorPreview,
  addStep,
  updateStepParams,
  toggleStepExpand,
  removeStep,
  clearAllSteps,
  handleImageSelect,
  handleSaveImage,
  startPointSelection,
  showFloodFillAnimation,
  handleDragStart,
  handleDragOver,
  handleDrop,
  handleDragEnd,
  startProcessing,

  initSocket,
  initIpcListeners,
  cleanup,
} = useColoring();

defineExpose({
  handleSaveImage,
  processing,
  imageLoaded,
});

onMounted(() => {
  initSocket();
  initIpcListeners();
});

onUnmounted(() => {
  cleanup();
});
</script>

<style scoped>
.coloring-layout {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  height: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: 8px;
  overflow: hidden;
  box-sizing: border-box;
}

/* ===== 管线区域 ===== */
.pipeline-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.pipeline-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(51, 65, 85, 0.3);
  border-bottom: 1px solid var(--border-color);
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.pipeline-icon {
  font-size: 18px;
  color: var(--primary-light);
}
.pipeline-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.pipeline-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 空状态 */
.empty-pipeline {
  flex: 1;
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
  opacity: 0.4;
}
.empty-pipeline p { margin: 0; text-align: center; }
.empty-pipeline .hint {
  font-size: 12px;
  margin-top: 8px;
  opacity: 0.7;
}

/* ===== 底部操作栏 ===== */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}
.action-right {
  display: flex;
  gap: 10px;
}

/* TransitionGroup 动画 */
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
