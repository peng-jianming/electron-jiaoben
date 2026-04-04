<template>
  <div class="task-select">
    <!-- 三栏布局：任务列表 | 已选任务 | 任务配置 -->
    <div class="task-columns">
      <!-- 左栏：可用任务列表 -->
      <div class="column column-tasks">
        <div class="column-header">
          <span class="column-title">
            <i class="column-icon">📋</i>
            可用任务
            <el-icon @click="emit('reload')"><Refresh /></el-icon>
          </span>
          <span class="column-badge">{{ taskList.length }}</span>
        </div>
        <div class="column-body">
          <div class="task-grid">
            <div
              v-for="name in taskList"
              :key="name"
              class="task-item"
              @click="addTask(name)"
            >
              <span class="task-name">{{ name }}</span>
              <span class="task-add-icon">+</span>
            </div>
            <div v-if="!taskList.length" class="empty-state">
              <span class="empty-icon">📭</span>
              <span class="empty-text">暂无任务</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中栏：已选任务队列 -->
      <div class="column column-selected">
        <div class="column-header">
          <span class="column-title">
            <i class="column-icon">✅</i>
            任务队列
          </span>
          <span class="column-badge" :class="{ active: selectedList.length }">
            {{ selectedList.length }}
          </span>
        </div>
        <div class="column-body">
          <VueDraggable
            v-if="selectedList.length"
            v-model="selectedList"
            :animation="150"
            handle=".drag-handle"
            class="selected-list"
          >
            <div
              v-for="(item, index) in selectedList"
              :key="item.id"
              class="selected-item"
              :class="{ active: currentConfigTask === item.id }"
              @click="selectItem(item)"
            >
              <span class="drag-handle" title="拖动排序">⋮⋮</span>
              <span class="order">{{ index + 1 }}</span>
              <span class="name">{{ item.name }}</span>
              <span
                class="remove-btn"
                title="移除"
                @click.stop="removeTask(item.id)"
              >×</span>
            </div>
          </VueDraggable>
          <div v-else class="empty-state">
            <span class="empty-icon">👈</span>
            <span class="empty-text">点击左侧添加任务</span>
          </div>
        </div>
      </div>

      <!-- 右栏：任务配置 -->
      <div class="column column-config">
        <div class="column-header">
          <span class="column-title">
            <i class="column-icon">⚙️</i>
            {{ currentSelectedItem ? currentSelectedItem.name + ' 配置' : '任务配置' }}
          </span>
        </div>
        <div class="column-body">
          <div
            v-if="currentSelectedItem && getTaskSchema(currentSelectedItem.name).length"
            class="config-form"
          >
            <div
              v-for="field in getTaskSchema(currentSelectedItem.name)"
              :key="field.key"
              class="config-row"
            >
              <label class="config-label">{{ field.label }}</label>
              <div class="config-control">
                <el-input-number
                  v-if="field.type === 'number'"
                  :model-value="getConfigValue(currentSelectedItem.id, field)"
                  :min="field.min"
                  :max="field.max"
                  :step="field.step ?? 1"
                  size="small"
                  controls-position="right"
                  @update:model-value="
                    (v) => setConfigValue(currentSelectedItem.id, field.key, v)
                  "
                />
                <el-input
                  v-else-if="field.type === 'text'"
                  :model-value="getConfigValue(currentSelectedItem.id, field)"
                  size="small"
                  @update:model-value="
                    (v) => setConfigValue(currentSelectedItem.id, field.key, v)
                  "
                />
                <el-select
                  v-else-if="field.type === 'select'"
                  :model-value="getConfigValue(currentSelectedItem.id, field)"
                  size="small"
                  :placeholder="'请选择' + field.label"
                  @update:model-value="
                    (v) => setConfigValue(currentSelectedItem.id, field.key, v)
                  "
                >
                  <el-option
                    v-for="opt in field.options || []"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
                <el-checkbox
                  v-else-if="field.type === 'checkbox'"
                  :model-value="getConfigValue(currentSelectedItem.id, field)"
                  @update:model-value="
                    (v) => setConfigValue(currentSelectedItem.id, field.key, v)
                  "
                >
                  启用
                </el-checkbox>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <span class="empty-icon">👆</span>
            <span class="empty-text">
              {{ currentSelectedItem ? '该任务无需配置' : '选择任务以配置' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { VueDraggable } from "vue-draggable-plus";
import { Refresh } from "@element-plus/icons-vue";
const props = defineProps({
  taskList: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:modelValue", "reload"]);

/**
 * 各任务的配置项 schema
 * 支持类型: number | text | select | checkbox
 */
const TASK_CONFIG_SCHEMA = {
  师门任务: [
    {
      key: "交易行最大金币购买需小于",
      label: "交易行最大金币购买需小于",
      default: 1000,
      type: "number",
      min: 0,
    },
  ],
  宝图任务: [{ key: "轮数", label: "轮数", default: 1, type: "number", min: 1, max: 99 }],
  抓鬼任务: [
    { key: "轮数", label: "轮数", default: 2, type: "number", min: 1, max: 99 },
    {
      key: "难度",
      label: "难度",
      default: "普通",
      type: "select",
      options: [
        { label: "简单", value: "简单" },
        { label: "普通", value: "普通" },
        { label: "困难", value: "困难" },
      ],
    },
    { key: "自动领双", label: "自动领双倍", default: true, type: "checkbox" },
  ],
};

function getTaskSchema(taskName) {
  return TASK_CONFIG_SCHEMA[taskName] || [];
}

function genId() {
  return "task-" + Date.now() + "-" + Math.random().toString(36).slice(2, 9);
}

/** 从 modelValue（任务配置列表数组）构建 selectedList + taskConfigById */
function buildFromModelValue(modelValue) {
  const arr = modelValue ?? props.modelValue ?? [];
  if (!Array.isArray(arr) || !arr.length) return { list: [], byId: {} };
  const list = arr.map((item) => ({ id: genId(), name: item.名称 }));
  const byId = {};
  list.forEach((item, i) => {
    byId[item.id] = arr[i].参数配置 != null ? { ...arr[i].参数配置 } : getDefaultConfig(item.name);
  });
  return { list, byId };
}

function getDefaultConfig(taskName) {
  const schema = getTaskSchema(taskName);
  const o = {};
  schema.forEach((f) => (o[f.key] = f.default));
  return o;
}

// 已选列表：每项带唯一 id，同一任务可出现多次
const { list: initialList, byId: initialConfig } = buildFromModelValue();
const selectedList = ref([...initialList]);
// 任务配置按 id 存储，每个「第几次」独立配置
const taskConfig = ref({ ...initialConfig });

// 当前选中的列表项 id（点击某一行即选中，下方展示该项的配置）
const currentConfigTask = ref("");
const currentSelectedItem = computed(
  () => selectedList.value.find((i) => i.id === currentConfigTask.value) ?? null
);
watch(
  selectedList,
  () => {
    const exists = selectedList.value.some((i) => i.id === currentConfigTask.value);
    if (!exists) currentConfigTask.value = "";
  },
  { deep: true }
);

watch(
  () => props.modelValue,
  (val) => {
    if (!Array.isArray(val) || !val.length) return;
    if (selectedList.value.length === 0) {
      const { list, byId } = buildFromModelValue(val);
      selectedList.value = [...list];
      taskConfig.value = { ...byId };
    }
  },
  { deep: true }
);

function syncToParent() {
  const 任务配置列表 = selectedList.value.map((i) => ({
    名称: i.name,
    参数配置: taskConfig.value[i.id] ?? getDefaultConfig(i.name),
  }));
  emit("update:modelValue", 任务配置列表);
}

watch(selectedList, () => syncToParent(), { deep: true });
watch(taskConfig, () => syncToParent(), { deep: true });

function selectItem(item) {
  currentConfigTask.value = item.id;
}

function addTask(name) {
  const id = genId();
  selectedList.value.push({ id, name });
  const schema = getTaskSchema(name);
  if (schema.length) {
    taskConfig.value = { ...taskConfig.value, [id]: getDefaultConfig(name) };
  }
  syncToParent();
}

function removeTask(id) {
  selectedList.value = selectedList.value.filter((i) => i.id !== id);
  if (taskConfig.value[id]) {
    const next = { ...taskConfig.value };
    delete next[id];
    taskConfig.value = next;
  }
  if (currentConfigTask.value === id) currentConfigTask.value = "";
  syncToParent();
}

function getConfigValue(itemId, field) {
  const c = taskConfig.value[itemId];
  let v = c?.[field.key];
  if (v === undefined || v === null || v === "") return field.default;
  if (field.type === "number") return Number(v);
  if (field.type === "checkbox") return Boolean(v);
  return v;
}

function setConfigValue(itemId, key, value) {
  const next = { ...taskConfig.value };
  if (!next[itemId]) next[itemId] = {};
  next[itemId] = { ...next[itemId], [key]: value };
  taskConfig.value = next;
  syncToParent();
}

</script>

<style scoped lang="less">
@column-header-height: 36px;
@task-select-height: 140px;
@border-color: #e4e7ed;
@bg-light: #f8f9fa;
@primary-color: #409eff;
@success-color: #67c23a;
@danger-color: #f56c6c;

.task-select {
  height: @task-select-height;
  min-height: @task-select-height;
  max-height: @task-select-height;
}

.task-columns {
  display: flex;
  height: 100%;
  gap: 12px;
}

// 通用列样式
.column {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  border: 1px solid @border-color;
  overflow: hidden;
}

.column-tasks {
  flex: 0 0 240px;
  min-width: 240px;
}

.column-selected {
  flex: 0 0 240px;
  min-width: 240px;
}

.column-config {
  flex: 1;
  min-width: 260px;
}

.column-header {
  height: @column-header-height;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  flex-shrink: 0;
}

.column-tasks .column-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.column-selected .column-header {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.column-config .column-header {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.column-title {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 6px;
}

.column-icon {
  font-style: normal;
  font-size: 13px;
}

.column-badge {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  
  &.active {
    background: rgba(255, 255, 255, 0.9);
    color: @success-color;
  }
}

.column-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #ddd;
    border-radius: 2px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: #ccc;
  }
}

// 任务网格
.task-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: @bg-light;
  border: 1px solid @border-color;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
  
  &:hover {
    border-color: @primary-color;
    background: #ecf5ff;
    
    .task-add-icon {
      background: @primary-color;
      color: #fff;
    }
  }
}

.task-name {
  color: #606266;
  font-weight: 500;
}

.task-add-icon {
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  background: #e4e7ed;
  color: #909399;
  border-radius: 4px;
  font-size: 14px;
  font-weight: bold;
  margin-left: 8px;
  transition: all 0.2s ease;
}

// 已选列表
.selected-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selected-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: @bg-light;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  
  &:hover {
    background: #e8f4ff;
  }
  
  &.active {
    border-color: @primary-color;
    background: #ecf5ff;
    
    .order {
      background: @primary-color;
    }
  }
}

.drag-handle {
  cursor: grab;
  color: #c0c4cc;
  font-size: 12px;
  user-select: none;
  
  &:active {
    cursor: grabbing;
  }
}

.order {
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  background: #909399;
  color: #fff;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
}

.name {
  flex: 1;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  width: 18px;
  height: 18px;
  line-height: 16px;
  text-align: center;
  color: #c0c4cc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s ease;
  
  &:hover {
    background: @danger-color;
    color: #fff;
  }
}

// 配置表单
.config-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  background: @bg-light;
  border-radius: 6px;
}

.config-label {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
  min-width: 100px;
  flex-shrink: 0;
}

.config-control {
  flex: 1;
  min-width: 0;
  
  :deep(.el-input-number) {
    width: 100%;
    max-width: 120px;
  }
  
  :deep(.el-input) {
    width: 100%;
  }
  
  :deep(.el-select) {
    width: 100%;
  }
  
  :deep(.el-checkbox) {
    height: 24px;
  }
}

// 空状态
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 60px;
  color: #c0c4cc;
}

.empty-icon {
  font-size: 20px;
  margin-bottom: 4px;
}

.empty-text {
  font-size: 11px;
}
</style>
