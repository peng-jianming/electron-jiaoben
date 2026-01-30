<template>
  <div>
    <el-table :data="list" border size="small" empty-text="没有发现账号~">
      <el-table-column type="index" label="序号"> </el-table-column>
      <el-table-column label="账号"> </el-table-column>
      <el-table-column label="设备"> </el-table-column>
      <el-table-column label="区服"> </el-table-column>
      <el-table-column label="职业"> </el-table-column>
      <el-table-column label="等级"> </el-table-column>
      <el-table-column label="金币"> </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="text" size="small">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from "vue";
const list = ref([]);
</script>

<style scoped></style>
