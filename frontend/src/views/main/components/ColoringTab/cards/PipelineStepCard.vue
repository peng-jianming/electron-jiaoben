<template>
  <div
    class="pipeline-step"
    :class="{ dragging: isDragging, completed: step.completed }"
    draggable="true"
    @dragstart="$emit('drag-start', index, $event)"
    @dragover.prevent="$emit('drag-over', index, $event)"
    @dragend="$emit('drag-end')"
    @drop="$emit('drop', index, $event)"
  >
    <!-- 步骤头部 -->
    <div class="step-header" @click="$emit('toggle-expand')">
      <div class="drag-handle">
        <el-icon><Rank /></el-icon>
      </div>
      <div class="step-number">{{ index + 1 }}</div>
      <div class="step-type-icon" :style="{ background: typeGradient }">
        <el-icon>
          <Brush v-if="step.type === 'color_filter'" />
          <MagicStick v-else-if="step.type === 'binary'" />
          <Aim v-else-if="step.type === 'flood_fill'" />
        </el-icon>
      </div>
      <div class="step-info">
        <span class="step-label">{{ typeLabel }}</span>
        <span class="step-summary">{{ summary }}</span>
      </div>
      <div class="step-actions">
        <el-icon v-if="step.completed" class="completed-icon"><Check /></el-icon>
        <el-button
          v-if="step.type === 'flood_fill' && step.completed"
          type="success" size="small" circle
          title="查看填充动画"
          @click.stop="$emit('show-animation', index, step)"
        >
          <el-icon><VideoPlay /></el-icon>
        </el-button>
        <el-icon class="expand-arrow" :class="{ expanded: step.expanded }">
          <ArrowDown />
        </el-icon>
        <el-button
          type="danger" size="small" circle
          class="delete-btn"
          @click.stop="$emit('remove')"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 参数面板（可折叠） -->
    <Transition name="expand">
      <div v-show="step.expanded" class="step-body">

        <!-- ===== 颜色过滤参数 ===== -->
        <template v-if="step.type === 'color_filter'">
          <div class="param-section">
            <div class="param-header">
              <span class="param-label">保留颜色</span>
              <el-button type="primary" size="small" :icon="Plus" circle @click="addKeepColor" />
            </div>
            <div class="color-rows">
              <div v-for="(color, i) in params.keepColors" :key="'k' + i" class="color-row">
                <div class="color-swatch" :style="{ backgroundColor: getColorPreview(color) }" />
                <el-input
                  :model-value="color"
                  placeholder="RRGGBB-容差"
                  @update:model-value="updateKeepColor(i, $event)"
                />
                <el-button type="danger" size="small" :icon="Delete" circle @click="removeKeepColor(i)" />
              </div>
            </div>
          </div>
          <div class="param-section">
            <div class="param-header">
              <span class="param-label">过滤颜色</span>
              <el-button type="primary" size="small" :icon="Plus" circle @click="addFilterColor" />
            </div>
            <div class="color-rows">
              <div v-for="(color, i) in params.filterColors" :key="'f' + i" class="color-row">
                <div class="color-swatch" :style="{ backgroundColor: getColorPreview(color) }" />
                <el-input
                  :model-value="color"
                  placeholder="RRGGBB-容差"
                  @update:model-value="updateFilterColor(i, $event)"
                />
                <el-button type="danger" size="small" :icon="Delete" circle @click="removeFilterColor(i)" />
              </div>
            </div>
          </div>
        </template>

        <!-- ===== 二值化参数 ===== -->
        <template v-if="step.type === 'binary'">
          <div class="param-section">
            <div class="threshold-header">
              <span class="param-label">阈值</span>
              <span class="threshold-value">{{ params.threshold }}</span>
            </div>
            <el-slider
              :model-value="params.threshold"
              :min="0" :max="255" :step="1"
              :marks="{ 0: '0', 127: '127', 255: '255' }"
              @update:model-value="emitParams({ threshold: $event })"
            />
          </div>
        </template>

        <!-- ===== 洪水填充参数 ===== -->
        <template v-if="step.type === 'flood_fill'">
          <div class="param-section flood-section">
            <div class="flood-row">
              <span class="param-label">X:</span>
              <el-input-number
                :model-value="params.x" :min="0" size="small" controls-position="right"
                @update:model-value="emitParams({ x: $event })"
              />
              <span class="param-label">Y:</span>
              <el-input-number
                :model-value="params.y" :min="0" size="small" controls-position="right"
                @update:model-value="emitParams({ y: $event })"
              />
              <el-button
                type="primary" size="small"
                :class="{ 'is-selecting': isSelectingPoint }"
                @click="$emit('select-point', step.id)"
              >
                <el-icon><Aim /></el-icon>
                <span>{{ isSelectingPoint ? '等待点击...' : '拾取坐标' }}</span>
              </el-button>
            </div>
          </div>
        </template>

      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import {
  Rank, Check, Delete, Plus, ArrowDown, VideoPlay,
  Brush, MagicStick, Aim,
} from '@element-plus/icons-vue';
import { STEP_TYPES } from '../../../composables/useColoring';

const props = defineProps({
  step: { type: Object, required: true },
  index: { type: Number, required: true },
  isDragging: Boolean,
  isSelectingPoint: Boolean,
  getColorPreview: { type: Function, required: true },
});

const emit = defineEmits([
  'update:params', 'remove', 'toggle-expand',
  'drag-start', 'drag-over', 'drag-end', 'drop',
  'show-animation', 'select-point',
]);

const params = computed(() => props.step.params);
const typeLabel = computed(() => STEP_TYPES[props.step.type]?.label ?? props.step.type);
const typeGradient = computed(() => STEP_TYPES[props.step.type]?.gradient ?? '#666');

const summary = computed(() => {
  const p = params.value;
  switch (props.step.type) {
    case 'color_filter': {
      const k = (p.keepColors || []).filter(c => c?.trim()).length;
      const f = (p.filterColors || []).filter(c => c?.trim()).length;
      return `保留 ${k} 个 · 过滤 ${f} 个`;
    }
    case 'binary':
      return `阈值 ${p.threshold}`;
    case 'flood_fill':
      return `起点 (${p.x}, ${p.y})`;
    default:
      return '';
  }
});

function emitParams(partial) {
  emit('update:params', { ...params.value, ...partial });
}

// ---------- 颜色过滤操作 ----------

function addKeepColor() {
  emitParams({ keepColors: [...(params.value.keepColors || []), ''] });
}
function removeKeepColor(i) {
  const arr = [...params.value.keepColors];
  arr.splice(i, 1);
  emitParams({ keepColors: arr });
}
function updateKeepColor(i, val) {
  const arr = [...params.value.keepColors];
  arr[i] = val;
  emitParams({ keepColors: arr });
}

function addFilterColor() {
  emitParams({ filterColors: [...(params.value.filterColors || []), ''] });
}
function removeFilterColor(i) {
  const arr = [...params.value.filterColors];
  arr.splice(i, 1);
  emitParams({ filterColors: arr });
}
function updateFilterColor(i, val) {
  const arr = [...params.value.filterColors];
  arr[i] = val;
  emitParams({ filterColors: arr });
}
</script>

<style scoped lang="less">
@primary: #6366f1;
@primary-light: #818cf8;
@success: #10b981;
@bg-card: #ffffff;
@text-primary: #1e293b;
@text-secondary: #64748b;
@text-muted: #94a3b8;
@border: #e2e8f0;

.pipeline-step {
  background: @bg-card;
  border-radius: 8px;
  border: 1px solid @border;
  transition: all 0.2s ease;
  overflow: hidden;
}

.pipeline-step:hover {
  border-color: #cbd5e1;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.pipeline-step.dragging {
  opacity: 0.5;
  border-color: @primary;
}

.pipeline-step.completed {
  border-color: rgba(16, 185, 129, 0.35);
  background: linear-gradient(135deg, @bg-card, rgba(16, 185, 129, 0.03));
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  cursor: pointer;
  user-select: none;
}

.drag-handle {
  color: @text-muted;
  cursor: grab;
  font-size: 14px;
}

.drag-handle:active {
  cursor: grabbing;
}

.step-number {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: @primary;
  color: #fff;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-type-icon {
  width: 24px;
  height: 24px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  flex-shrink: 0;
}

.step-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.step-label {
  font-size: 13px;
  font-weight: 500;
  color: @text-primary;
}

.step-summary {
  font-size: 11px;
  color: @text-muted;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.completed-icon {
  color: @success;
  font-size: 16px;
}

.expand-arrow {
  color: @text-muted;
  font-size: 12px;
  transition: transform 0.2s ease;
}

.expand-arrow.expanded {
  transform: rotate(180deg);
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.15s;
}

.pipeline-step:hover .delete-btn {
  opacity: 1;
}

.step-body {
  padding: 0 10px 10px;
}

.param-section {
  margin-bottom: 12px;
}

.param-section:last-child {
  margin-bottom: 0;
}

.param-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.param-label {
  font-size: 12px;
  font-weight: 500;
  color: @text-secondary;
}

.color-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.color-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.color-swatch {
  width: 24px;
  height: 24px;
  border-radius: 5px;
  border: 1.5px solid @border;
  flex-shrink: 0;
}

.color-row :deep(.el-input) {
  flex: 1;
}

.threshold-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.threshold-value {
  font-size: 18px;
  font-weight: 600;
  color: @primary;
}

.flood-section {
  padding-top: 2px;
}

.flood-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.flood-row :deep(.el-input-number) {
  width: 100px;
}

.is-selecting {
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.3); }
  50% { box-shadow: 0 0 0 5px rgba(99, 102, 241, 0); }
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

:deep(.el-slider__runway) {
  background: @border;
}

:deep(.el-slider__bar) {
  background: linear-gradient(90deg, @primary, @primary-light);
}

:deep(.el-slider__button) {
  border-color: @primary;
}
</style>
