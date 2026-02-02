<template>
  <div>
    <el-table
      v-loading="loading"
      :data="list"
      border
      size="small"
      height="700"
      empty-text="没有发现账号~"
    >
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column prop="account" label="账号" min-width="100" />
      <el-table-column prop="device" label="设备" min-width="80" />
      <el-table-column prop="server" label="区服" min-width="80" />
      <el-table-column prop="job" label="职业" min-width="80" />
      <el-table-column prop="level" label="等级" width="70" />
      <el-table-column prop="gold" label="金币" width="90" />
      <el-table-column label="操作" fixed="right">
        <template #default="scope">
          <el-button
            type="danger"
            size="small"
            @click="handleDelete(scope.$index)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";

const list = ref([]);
const loading = ref(false);

async function loadList() {
  if (!ipc) return;
  loading.value = true;
  try {
    const res = await ipc.invoke(ipcApiRoute.获取账号列表);
    list.value = Array.isArray(res) ? res : [];
  } catch (e) {
    list.value = [];
    ElMessage.error("加载账号列表失败");
  } finally {
    loading.value = false;
  }
}

async function handleDelete(index) {
  try {
    await ElMessageBox.confirm("确定删除该账号？", "提示", {
      type: "warning",
      confirmButtonText: "确定",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
  if (!ipc) return;
  try {
    const ok = await ipc.invoke(ipcApiRoute.删除账号, { index });
    if (ok) {
      ElMessage.success("已删除");
      await loadList();
    } else {
      ElMessage.error("删除失败");
    }
  } catch (e) {
    ElMessage.error("删除失败");
  }
}

onMounted(() => {
  
  loadList();
});
</script>

<style scoped></style>
