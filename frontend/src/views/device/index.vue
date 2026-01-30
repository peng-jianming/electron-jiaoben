<template>
  <div>
    <el-table :data="list" border size="small" empty-text="没有发现设备~">
      <el-table-column type="selection" width="55"> </el-table-column>
      <el-table-column type="index" label="序号"> </el-table-column>
      <el-table-column label="设备"> </el-table-column>
      <el-table-column label="账号"> </el-table-column>
      <el-table-column label="即将执行的操作"> </el-table-column>
      <el-table-column label="当前在操作"> </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="text" size="small">开始</el-button>
          <el-button type="text" size="small">结束</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-button>设备检测</el-button>
  </div>
</template>

<script setup>
import { ref } from "vue";
const list = ref([]);
</script>

<style scoped></style>
