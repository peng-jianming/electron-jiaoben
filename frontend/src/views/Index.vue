<template>
  <div class="app-container">
    <TitleBar title="咚咚锵" />

    <div class="main-wrapper">
      <!-- 左侧导航栏 -->
      <aside class="sidebar">
        <div class="nav-menu">
          <div
            v-for="(value, key) in map"
            :key="key"
            class="nav-item"
            :class="{ active: currentTab === key }"
            @click="currentTab = key"
          >
            <span class="nav-label">{{ value.name }}</span>
          </div>
        </div>

        <!-- 底部状态指示 -->
        <div class="sidebar-footer">
          <div class="status-indicator">
            <span
              class="status-dot"
              :class="{ online: isBackendReady, waiting: !isBackendReady }"
            ></span>
            <span class="status-text">{{
              isBackendReady ? "已连接" : "等待后端" 
            }}</span>
          </div>
        </div>
      </aside>

      <!-- 主内容区域 -->
      <main class="main-content">
        <!-- 内容面板 -->
        <div class="content-panel">
          <component
            v-for="(value, key) in map"
            v-show="currentTab === key"
            :key="key"
            :is="value.component"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import TitleBar from "@/components/TitleBar.vue";
import { Monitor, User, List, Refresh } from "@element-plus/icons-vue";
import ImageProcessing from "@/components/image-processing/index.vue";
import FloodFill from "@/components/flood-fill/index.vue";
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { storeToRefs } from "pinia";
import { useImageProcessingStore } from "@/stores/imageProcessing";

const currentTab = ref("image-processing");
const imageProcessingStore = useImageProcessingStore();
const {isBackendReady } = storeToRefs(imageProcessingStore);

const map = computed(() => {
  return {
    "image-processing": {
      name: "图像处理",
      component: ImageProcessing,
    },
    "flood-fill": {
      name: "洪水填充",
      component: FloodFill,
    },
  };
});

onMounted(async () => {
  // matchSocket 已在 main.js 连接成功后才挂载页面
});
</script>

<style lang="less">
// 变量定义
@sidebar-width: 72px;
@title-bar-height: 40px;
@stats-bar-height: 80px;
@panel-header-height: 50px;
@primary-color: #5b6af0;
@success-color: #22c55e;
@warning-color: #f59e0b;
@danger-color: #ef4444;
@bg-color: #f1f5f9;
@card-bg: #ffffff;
@text-primary: #1e293b;
@text-secondary: #475569;
@text-muted: #94a3b8;
@border-color: #e2e8f0;

html,
body,
#app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB",
    "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
}

.app-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  background-color: @bg-color;
}

.main-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
  height: calc(100vh - @title-bar-height);
}

// 左侧导航栏
.sidebar {
  width: @sidebar-width;
  background: #ffffff;
  border-right: 1px solid @border-color;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex-shrink: 0;
}

.nav-menu {
  padding-top: 12px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 14px 0;
  margin: 4px 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  color: @text-muted;
  position: relative;

  &:hover {
    color: @primary-color;
    background: rgba(91, 106, 240, 0.06);
  }

  &.active {
    color: @primary-color;
    background: linear-gradient(
      135deg,
      rgba(91, 106, 240, 0.12) 0%,
      rgba(139, 92, 246, 0.08) 100%
    );

    .el-icon {
      transform: scale(1.05);
    }
  }
}

.nav-label {
  font-size: 11px;
  margin-top: 5px;
  font-weight: 500;
}

.sidebar-footer {
  padding: 12px 8px;
  border-top: 1px solid @border-color;
}

.status-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border-radius: 8px;
  background: #f8fafc;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: @danger-color;

  &.online {
    background-color: @success-color;
    box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
    animation: pulse 2s infinite;
  }

  &.waiting {
    background-color: @warning-color;
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
    animation: pulse 1s infinite;
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.status-text {
  font-size: 10px;
  color: @text-muted;
  font-weight: 500;
}

// 主内容区域
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 15px;
  overflow: hidden;
  gap: 15px;
}

// 内容面板
.content-panel {
  flex: 1;
  background: @card-bg;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  border: 1px solid @border-color;
}

.panel-header {
  height: @panel-header-height;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid @border-color;
  flex-shrink: 0;
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: @text-primary;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;

  .el-icon {
    color: @primary-color;
    background: rgba(91, 106, 240, 0.1);
    padding: 6px;
    border-radius: 8px;
  }
}

.panel-actions {
  display: flex;
  gap: 10px;
}

.panel-body {
  flex: 1;
  padding: 15px;
  overflow: hidden;
}

// 任务配置页面全屏样式
.task-select-full {
  height: 100% !important;
  min-height: unset !important;
  max-height: unset !important;

  :deep(.task-columns) {
    height: 100%;
  }

  :deep(.column) {
    flex: 1;
    min-width: 200px;
  }

  :deep(.column-tasks) {
    flex: 0 0 30%;
  }

  :deep(.column-selected) {
    flex: 0 0 25%;
  }

  :deep(.column-config) {
    flex: 1;
  }
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// Element Plus 组件样式覆盖
:deep(.el-button) {
  border-radius: 6px;
}

:deep(.el-table) {
  border-radius: 6px;

  th.el-table__cell {
    background-color: #fafafa;
    color: @text-secondary;
    font-weight: 500;
  }
}

:deep(.el-tag) {
  border-radius: 4px;
}
</style>
