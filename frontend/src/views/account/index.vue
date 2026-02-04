<template>
  <div class="account-container">
    <div class="table-container">
      <el-table 
        :data="list" 
        border 
        size="small" 
        height="100%" 
        empty-text="没有发现账号~"
        stripe
        highlight-current-row
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="账号" label="账号" min-width="120" show-overflow-tooltip />
        <el-table-column prop="名字" label="名字" min-width="120" show-overflow-tooltip />
        <el-table-column prop="区服" label="区服" width="100" show-overflow-tooltip />
        <el-table-column prop="职业" label="职业" width="100" show-overflow-tooltip />
        <el-table-column prop="等级" label="等级" width="80" align="center" />
        <el-table-column prop="金币" label="金币" width="100" />
        <el-table-column prop="更新时间" label="更新时间" width="160" show-overflow-tooltip>
            <template #default="scope">
                {{ scope.row.更新时间 ? new Date(scope.row.更新时间).toLocaleString() : '-' }}
            </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="scope">
            <el-button
              link
              type="danger"
              size="small"
              @click="emit('deleteAccount', scope.$index)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from "vue";

const props = defineProps({
  list: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["deleteAccount"]);
</script>

<style scoped lang="less">
.account-container {
    height: 100%;
    display: flex;
    flex-direction: column;
}
.table-container {
    flex: 1;
    overflow: hidden;
}
</style>
