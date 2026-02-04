<template>
  <div class="task-select">
    <el-card shadow="never" class="task-card">
      <template #header>
        <span>任务选择与配置</span>
        <span class="tip"></span>
      </template>

      <div class="section">
        <div class="section-title">任务列表</div>
        <div class="task-add-buttons">
          <el-button
            v-for="name in taskList"
            :key="name"
            type="primary"
            plain
            size="small"
            @click="addTask(name)"
          >
            {{ name }} · 添加
          </el-button>
          <span v-if="!taskList.length" class="empty-tip"
            >暂无任务，请先获取任务列表</span
          >
        </div>
      </div>

      <!-- 已选任务顺序（可重复，可拖动排序） -->
      <div class="section" v-if="selectedList.length">
        <div class="section-title">已选任务</div>
        <VueDraggable
          v-model="selectedList"
          :animation="150"
          handle=".drag-handle"
          class="selected-list"
        >
          <div
            v-for="(item, index) in selectedList"
            :key="item.id"
            class="selected-item"
            :class="{ 'is-config-target': currentConfigTask === item.id }"
            @click="selectItem(item)"
          >
            <span class="drag-handle" title="拖动排序" @click.stop>⋮⋮</span>
            <span class="order">{{ index + 1 }}</span>
            <span class="name">{{ item.name }}</span>
            <el-button
              type="danger"
              link
              size="small"
              class="remove-btn"
              @click.stop="removeTask(item.id)"
            >
              移除
            </el-button>
          </div>
        </VueDraggable>
      </div>

      <!-- 任务配置：当前选中的那一项有配置时，在此展示 -->
      <div
        class="section config-section"
        v-if="currentSelectedItem && getTaskSchema(currentSelectedItem.name).length"
      >
        <div class="section-title">
          任务配置（当前选中：{{ currentSelectedItem.name }}）
        </div>
        <div class="config-area">
          <div class="config-panel">
            <div class="config-form">
              <div
                v-for="field in getTaskSchema(currentSelectedItem.name)"
                :key="field.key"
                class="config-row"
                :class="{ 'config-row--checkbox': field.type === 'checkbox' }"
              >
                <label v-if="field.type !== 'checkbox'" class="config-label">{{
                  field.label
                }}</label>
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
                    class="config-select"
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
                    {{ field.label }}
                  </el-checkbox>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { VueDraggable } from "vue-draggable-plus";

const props = defineProps({
  taskList: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: Object,
    default: () => ({ selectedTasks: [], taskConfig: {} }),
  },
});

const emit = defineEmits(["update:modelValue"]);

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

/** 从 modelValue 构建 selectedList + taskConfigById（兼容旧格式：taskConfig 按任务名 或 按顺序数组） */
function buildFromModelValue() {
  const tasks = props.modelValue?.selectedTasks || [];
  const config = props.modelValue?.taskConfig;
  const list = tasks.map((name) => ({ id: genId(), name }));
  const byId = {};
  if (Array.isArray(config)) {
    list.forEach((item, i) => {
      byId[item.id] = config[i] != null ? { ...config[i] } : getDefaultConfig(item.name);
    });
  } else {
    const used = {};
    list.forEach((item) => {
      const fromName = config?.[item.name];
      const key = item.name;
      if (fromName && !used[key]) {
        used[key] = true;
        byId[item.id] = { ...fromName };
      } else {
        byId[item.id] = getDefaultConfig(item.name);
      }
    });
  }
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

// 同步到父组件：selectedTasks 为名称顺序数组，taskConfig 为同顺序的配置数组（便于后端按顺序使用）
function syncToParent() {
  const names = selectedList.value.map((i) => i.name);
  const configArray = selectedList.value.map(
    (i) => taskConfig.value[i.id] ?? getDefaultConfig(i.name)
  );
  emit("update:modelValue", {
    selectedTasks: names,
    taskConfig: configArray,
  });
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
.task-select {
  margin-bottom: 16px;
}
.task-card {
  border-radius: 8px;
  .tip {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-left: 8px;
  }
}
.section {
  margin-bottom: 16px;
  &:last-child {
    margin-bottom: 0;
  }
}
.section-title {
  font-size: 13px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}
.task-add-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  .empty-tip {
    color: var(--el-text-color-placeholder);
    font-size: 12px;
  }
}
.selected-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.selected-item {
  display: flex;
  align-items: center;
  gap: 8px 12px;
  padding: 8px 10px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  &.is-config-target {
    outline: 1px solid var(--el-color-primary-light-5);
    background: var(--el-color-primary-light-9);
  }
  .drag-handle {
    cursor: grab;
    color: var(--el-text-color-placeholder);
    font-size: 14px;
    user-select: none;
    padding: 0 2px;
    &:active {
      cursor: grabbing;
    }
  }
  .order {
    width: 22px;
    height: 22px;
    line-height: 22px;
    text-align: center;
    background: var(--el-color-primary);
    color: #fff;
    border-radius: 4px;
    font-size: 12px;
    flex-shrink: 0;
  }
  .name {
    min-width: 80px;
    font-weight: 500;
    flex: 1;
  }
  .remove-btn {
    margin-left: auto;
  }
}

.config-section {
  border-top: 1px dashed var(--el-border-color-lighter);
  padding-top: 14px;
}
.config-area {
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  padding: 12px 14px;
}
.config-panel {
  padding: 4px 0 0;
}
.config-form {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px 24px;
  max-width: 720px;
}
.config-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  .config-label {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    white-space: nowrap;
    flex-shrink: 0;
    width: 120px;
  }
  .config-control {
    flex: 1;
    min-width: 0;
    .el-input-number {
      width: 120px;
    }
    .el-input {
      width: 100%;
      min-width: 100px;
    }
    .config-select {
      width: 100%;
      min-width: 120px;
    }
  }
  &.config-row--checkbox .config-control {
    flex: none;
  }
}
</style>
