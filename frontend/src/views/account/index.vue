<template>
  <div>
    <el-table :data="list" border size="small" height="700" empty-text="没有发现账号~">
      <el-table-column type="index" label="序号" />
      <el-table-column prop="账号" label="账号" />
      <el-table-column prop="名字" label="名字" />
      <el-table-column prop="区服" label="区服" />
      <el-table-column prop="职业" label="职业" />
      <el-table-column prop="等级" label="等级" />
      <el-table-column prop="金币" label="金币" />
      <el-table-column prop="更新时间" label="更新时间" />
      <el-table-column label="操作">
        <template #default="scope">
          <el-button
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

<style scoped></style>
