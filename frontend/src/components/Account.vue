<template>
  <div class="account-container">
    <!-- 操作按钮栏 -->
    <div class="toolbar-section">
      <div class="task-info">
        <span class="task-info-label">已选任务：</span>
        <span v-if="taskSelectValue.selectedTasks.length" class="task-info-value">
          {{ taskSelectValue.selectedTasks.join(" → ") }}
        </span>
        <span v-else class="task-info-empty">未选择任务，请到"任务"页面配置</span>
      </div>
      <div class="action-buttons">
        <el-button
          type="primary"
          @click="handleBatchStart"
          :disabled="!taskSelectValue.selectedTasks.length"
        >全部开始</el-button>
        <el-button type="warning" @click="emit('batchPause')">全部暂停</el-button>
        <el-button type="success" @click="emit('batchResume')">全部恢复</el-button>
        <el-button type="danger" @click="emit('batchEnd')">全部结束</el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table
        :data="list"
        row-key="账号"
        :expand-row-keys="expandedRowKeys"
        @expand-change="onExpandChange"
        :row-class-name="tableRowClassName"
        border
        size="small"
        empty-text="没有发现账号~"
        height="100%"
        stripe
        highlight-current-row
      >
        <el-table-column type="expand" label="日志">
          <template #default="props">
            <div class="log-container">
              <div class="log-content" v-if="props.row.日志?.length">
                <div
                  v-for="(log, index) in props.row.日志.slice().reverse()"
                  :key="index"
                  class="log-item"
                  :class="getLogClass(log)"
                >
                  <span class="log-index">#{{ props.row.日志.length - index }}</span>
                  <span class="log-text">{{ log }}</span>
                </div>
              </div>
              <div class="log-empty" v-else>
                <svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor">
                  <path d="M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10zm-8-4h2v2h-2v-2zm0-6h2v4h-2V8z"/>
                </svg>
                <span>暂无日志信息</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="账号" label="账号" min-width="120" show-overflow-tooltip />
        <el-table-column label="名字" min-width="100" show-overflow-tooltip>
          <template #default="scope">
            {{ scope.row.名字 || scope.row.角色名 || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="设备ID" min-width="150" show-overflow-tooltip>
          <template #default="scope">
            <span v-if="scope.row.状态 === '等待设备'" class="waiting-device">
              <el-icon class="waiting-icon"><Loading /></el-icon>
              等待空闲设备
            </span>
            <span v-else-if="scope.row.设备ID" class="device-id">{{ scope.row.设备ID }}</span>
            <span v-else class="no-device">-</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="110" align="center">
          <template #default="scope">
            <el-tag
              :type="getStatusType(scope.row.状态)"
              size="small"
              effect="light"
            >{{ scope.row.状态 || '空闲' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="当前任务" label="当前任务" min-width="120" show-overflow-tooltip />

        <el-table-column label="操作" width="250" fixed="right" align="center">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              :disabled="!props.taskSelectValue.selectedTasks.length || isRunning(scope.row)"
              @click="handleStart(scope.row)"
            >开始</el-button>
            <el-button
              type="warning"
              size="small"
              :disabled="scope.row.状态 !== '运行中'"
              @click="emit('pauseTask', scope.row)"
            >暂停</el-button>
            <el-button
              type="success"
              size="small"
              :disabled="scope.row.状态 !== '已暂停'"
              @click="emit('resumeTask', scope.row)"
            >恢复</el-button>
            <el-button
              type="danger"
              size="small"
              :disabled="!isActive(scope.row)"
              @click="emit('endTask', scope.row)"
            >结束</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 统计信息 -->
    <div class="statistics-info">
      <div class="statistics-info-item statistics-info-item--total">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">总账号</span>
          <span class="statistics-info-item-value">{{ list.length }}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--running">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">运行中</span>
          <span class="statistics-info-item-value">{{ list.filter(r => r.状态 === '运行中').length }}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--paused">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">已暂停</span>
          <span class="statistics-info-item-value">{{ list.filter(r => r.状态 === '已暂停').length }}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--waiting">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">等待设备</span>
          <span class="statistics-info-item-value">{{ list.filter(r => r.状态 === '等待设备').length }}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--idle">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">空闲</span>
          <span class="statistics-info-item-value">{{ list.filter(r => !r.状态 || r.状态 === '空闲').length }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { Loading } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  list: {
    type: Array,
    default: () => [],
  },
  taskSelectValue: {
    type: Object,
    default: () => ({ selectedTasks: [], taskConfig: {} }),
  },
});

const emit = defineEmits([
  "startTask",
  "pauseTask",
  "resumeTask",
  "endTask",
  "batchStart",
  "batchPause",
  "batchResume",
  "batchEnd",
]);

const expandedRowKeys = ref([]);
watch(
  () => props.list,
  (list) => {
    expandedRowKeys.value = expandedRowKeys.value.filter((key) =>
      list.some((row) => row.账号 === key)
    );
  },
  { deep: true }
);

function onExpandChange(_row, expandedRows) {
  expandedRowKeys.value = expandedRows.map((r) => r.账号);
}

function isRunning(row) {
  return row.状态 === '运行中' || row.状态 === '已暂停' || row.状态 === '等待设备';
}

function isActive(row) {
  return row.状态 === '运行中' || row.状态 === '已暂停' || row.状态 === '等待设备';
}

const tableRowClassName = ({ row }) => {
  if (row.故障) return "fault-row";
  return "";
};

function handleStart(row) {
  const { selectedTasks } = props.taskSelectValue;
  if (!selectedTasks.length) {
    ElMessage.warning("请先到「任务」页面选择任务");
    return;
  }
  emit("startTask", row);
}

function handleBatchStart() {
  const { selectedTasks } = props.taskSelectValue;
  if (!selectedTasks.length) {
    ElMessage.warning("请先到「任务」页面选择任务");
    return;
  }
  emit("batchStart");
}

function getStatusType(status) {
  const map = {
    "运行中": "success",
    "已暂停": "warning",
    "等待设备": "info",
    "空闲": "",
  };
  return map[status] || "";
}

function getLogClass(log) {
  if (!log) return "";
  if (log.includes("错误") || log.includes("error") || log.includes("失败")) return "log-error";
  if (log.includes("警告") || log.includes("warn")) return "log-warn";
  if (log.includes("成功") || log.includes("完成") || log.includes("success")) return "log-success";
  return "";
}
</script>

<style scoped lang="less">
@primary-color: #5b6af0;
@success-color: #22c55e;
@warning-color: #f59e0b;
@danger-color: #ef4444;
@border-color: #e2e8f0;
@text-primary: #1e293b;
@text-secondary: #475569;
@text-muted: #94a3b8;
@bg-light: #f8fafc;

.account-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

// ─── 工具栏 ────────────────────────────────
.toolbar-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  flex-shrink: 0;
  padding-bottom: 12px;
  border-bottom: 1px solid @border-color;
  margin-bottom: 12px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.task-info-label {
  font-size: 13px;
  color: @text-secondary;
  flex-shrink: 0;
}

.task-info-value {
  font-size: 13px;
  color: @primary-color;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-info-empty {
  font-size: 13px;
  color: @text-muted;
  font-style: italic;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  flex-shrink: 0;

  :deep(.el-button) {
    border-radius: 8px;
    font-weight: 500;
    font-size: 13px;
    padding: 8px 16px;
    transition: all 0.25s ease;

    &--primary {
      background: linear-gradient(135deg, @primary-color 0%, #8b5cf6 100%);
      border: none;
      box-shadow: 0 2px 8px rgba(91, 106, 240, 0.25);
      &:hover { background: linear-gradient(135deg, #4f5bd5 0%, #7c4ddb 100%); box-shadow: 0 4px 12px rgba(91, 106, 240, 0.35); transform: translateY(-1px); }
    }
    &--success {
      background: linear-gradient(135deg, @success-color 0%, #4ade80 100%);
      border: none;
      box-shadow: 0 2px 8px rgba(34, 197, 94, 0.25);
      &:hover { background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%); box-shadow: 0 4px 12px rgba(34, 197, 94, 0.35); transform: translateY(-1px); }
    }
    &--warning {
      background: linear-gradient(135deg, @warning-color 0%, #fbbf24 100%);
      border: none;
      box-shadow: 0 2px 8px rgba(245, 158, 11, 0.25);
      &:hover { background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35); transform: translateY(-1px); }
    }
    &--danger {
      background: linear-gradient(135deg, @danger-color 0%, #f87171 100%);
      border: none;
      box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25);
      &:hover { background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35); transform: translateY(-1px); }
    }
  }
}

// ─── 表格 ──────────────────────────────────
.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;

  :deep(.el-table) {
    border-radius: 10px;
    border: 1px solid @border-color;

    th.el-table__cell {
      background-color: @bg-light !important;
      border-bottom: 1px solid @border-color !important;
      color: @text-secondary;
      font-weight: 600;
      font-size: 13px;
    }

    .el-table__row {
      transition: background-color 0.2s ease;
      &:hover > td { background-color: #f5f7fa !important; }
    }

    .el-table__row.fault-row > td {
      animation: fault-row-blink 1s ease-in-out infinite;
    }

    .el-tag {
      border-radius: 6px;
      font-weight: 500;
      padding: 0 10px;
      transition: none;
    }

    .el-button { border-radius: 6px; }
  }
}

.waiting-device {
  color: @warning-color;
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.waiting-icon {
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.device-id {
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 12px;
  color: @text-secondary;
}

.no-device {
  color: @text-muted;
}

// ─── 统计栏 ────────────────────────────────
.statistics-info {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  flex-shrink: 0;
  padding-top: 6px;
  margin-top: 8px;
  border-top: 1px solid @border-color;
}

.statistics-info-item {
  position: relative;
  padding: 6px 10px;
  margin: 2px;
  border-radius: 8px;
  background: #f9fafb;
  border: 1px solid fade(@border-color, 50%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  display: flex;
  align-items: center;
  overflow: hidden;
  transition: all 0.15s ease;

  &:hover { transform: translateY(-1px); box-shadow: 0 4px 8px rgba(15, 23, 42, 0.08); }
}

.statistics-info-item-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.statistics-info-item-label {
  font-size: 11px;
  color: @text-muted;
}

.statistics-info-item-value {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #1f2933;
}

.statistics-info-item--total {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border-color: rgba(91, 106, 240, 0.3);
  .statistics-info-item-value { color: @primary-color; }
}
.statistics-info-item--running {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-color: rgba(34, 197, 94, 0.3);
  .statistics-info-item-value { color: @success-color; }
}
.statistics-info-item--paused {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-color: rgba(245, 158, 11, 0.3);
  .statistics-info-item-value { color: @warning-color; }
}
.statistics-info-item--waiting {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-color: rgba(59, 130, 246, 0.3);
  .statistics-info-item-value { color: #3b82f6; }
}
.statistics-info-item--idle {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-color: rgba(148, 163, 184, 0.3);
  .statistics-info-item-value { color: @text-secondary; }
}

@keyframes fault-row-blink {
  0%, 100% { background-color: #fff5f5; }
  50% { background-color: #ffe1e1; }
}

// ─── 日志 ──────────────────────────────────
.log-container {
  background: @bg-light;
  border-radius: 10px;
  margin: 0 5px;
  overflow: hidden;
  border: 1px solid @border-color;
}

.log-content {
  height: 220px;
  overflow-y: auto;
  padding: 8px;

  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; &:hover { background: #94a3b8; } }
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #fff;
  border-radius: 8px;
  border-left: 3px solid @border-color;
  transition: all 0.2s ease;

  &:hover { background: #f8fafc; transform: translateX(2px); }
  &:last-child { margin-bottom: 0; }

  &.log-error {
    border-left-color: @danger-color;
    background: linear-gradient(90deg, #fef2f2 0%, #fff 30%);
    .log-index { background: #fef2f2; color: @danger-color; }
  }
  &.log-warn {
    border-left-color: @warning-color;
    background: linear-gradient(90deg, #fffbeb 0%, #fff 30%);
    .log-index { background: #fffbeb; color: @warning-color; }
  }
  &.log-success {
    border-left-color: @success-color;
    background: linear-gradient(90deg, #f0fdf4 0%, #fff 30%);
    .log-index { background: #f0fdf4; color: @success-color; }
  }
}

.log-index {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 600;
  color: @text-muted;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
}

.log-text {
  flex: 1;
  font-size: 12px;
  color: @text-secondary;
  line-height: 1.5;
  word-break: break-all;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
}

.log-empty {
  height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: @text-muted;

  svg { opacity: 0.4; }
  span { font-size: 13px; }
}
</style>
