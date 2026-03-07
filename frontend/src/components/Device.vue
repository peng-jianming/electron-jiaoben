<template>
  <div class="device-container">
    <div class="table-container">
      <el-table :data="list" row-key="设备ID" border size="small" empty-text="没有发现设备~" height="100%" stripe
        highlight-current-row>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column label="设备ID" prop="设备ID" show-overflow-tooltip min-width="200" />
        <el-table-column label="状态" width="120" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.状态 === '空闲' ? 'success' : 'warning'" size="small" effect="light">{{ scope.row.状态 ||
              '空闲' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="占用账号" prop="占用账号" min-width="150" show-overflow-tooltip>
          <template #default="scope">
            <span v-if="scope.row.占用账号" class="occupied-account">{{ scope.row.占用账号 }}</span>
            <span v-else class="no-account">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="310" fixed="right" align="center">
          <template #default="scope">
            <el-button v-if="scope.row.是否禁用"  type="success" size="small">启用</el-button>
            <el-button v-else type="danger" size="small">禁用</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 统计信息 -->
    <div class="statistics-info">
      <div class="statistics-info-item statistics-info-item--total">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">总设备数</span>
          <span class="statistics-info-item-value">{{ list.length }}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--idle">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">空闲设备</span>
          <span class="statistics-info-item-value">{{list.filter(d => d.状态 === '空闲').length}}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--occupied">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">占用设备</span>
          <span class="statistics-info-item-value">{{list.filter(d => d.状态 === '占用').length}}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  list: {
    type: Array,
    default: () => [],
  },
});
</script>

<style scoped lang="less">
@primary-color: #5b6af0;
@success-color: #22c55e;
@warning-color: #f59e0b;
@border-color: #e2e8f0;
@text-primary: #1e293b;
@text-secondary: #475569;
@text-muted: #94a3b8;
@bg-light: #f8fafc;

.device-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

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

      &:hover>td {
        background-color: #f5f7fa !important;
      }
    }

    .el-tag {
      border-radius: 6px;
      font-weight: 500;
      padding: 0 10px;
      transition: none;
    }
  }
}

.occupied-account {
  font-size: 12px;
  color: @text-secondary;
}

.no-account {
  color: @text-muted;
}

// ─── 统计栏 ────────────────────────────────
.statistics-info {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(15, 23, 42, 0.08);
  }
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

  .statistics-info-item-value {
    color: @primary-color;
  }
}

.statistics-info-item--idle {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-color: rgba(34, 197, 94, 0.3);

  .statistics-info-item-value {
    color: @success-color;
  }
}

.statistics-info-item--occupied {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border-color: rgba(245, 158, 11, 0.3);

  .statistics-info-item-value {
    color: @warning-color;
  }
}
</style>
