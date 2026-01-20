<template>
  <div class="image-processor">
    <!-- Tab 切换 -->
    <el-tabs 
      v-model="activeTab" 
      type="border-card"
    >
      <!-- 图片处理 Tab -->
      <el-tab-pane label="图片处理" name="image-processor">
      </el-tab-pane>

      <!-- 调色 Tab -->
      <el-tab-pane label="调色" name="coloring">
      </el-tab-pane>

      <!-- 寻路测试 Tab -->
      <el-tab-pane label="寻路测试" name="pathfinding">
      </el-tab-pane>
    </el-tabs>

    <!-- 子路由内容 -->
    <div class="router-view-container">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component 
            :is="Component" 
            ref="currentComponentRef"
          />
        </transition>
      </router-view>
    </div>

    <!-- 处理状态指示器 -->
    <transition name="fade">
      <div v-if="isProcessing" class="processing-indicator">
        <div class="spinner"></div>
        <span>处理中...</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, watchEffect, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

// Tab 切换 - 从路由获取当前激活的 tab
const activeTab = computed({
  get: () => {
    const routeName = route.name;
    if (routeName === 'Coloring') return 'coloring';
    if (routeName === 'Pathfinding') return 'pathfinding';
    return 'image-processor'; // 默认或 ImageProcessor
  },
  set: (value) => {
    // Tab 切换时更新路由
    const routeName = value === 'image-processor' ? 'ImageProcessor' : value === 'coloring' ? 'Coloring' : 'Pathfinding';
    router.push({ name: routeName });
  }
});

// 处理状态
const isProcessing = ref(false);
const currentComponentRef = ref(null);

// 监听组件实例的 processing 状态
let stopWatcher = null;

watchEffect(() => {
  if (currentComponentRef.value) {
    const component = currentComponentRef.value;
    
    // 如果组件暴露了 processing 属性（如 ColoringTab）
    if (component.processing !== undefined) {
      // processing 是通过 defineExpose 暴露的 ref，需要监听其 .value
      if (typeof component.processing === 'object' && 'value' in component.processing) {
        // 清理之前的 watcher
        if (stopWatcher) {
          stopWatcher();
        }
        stopWatcher = watch(
          () => component.processing.value,
          (newVal) => {
            isProcessing.value = newVal;
          },
          { immediate: true }
        );
      } else {
        // 如果是普通值，直接使用
        isProcessing.value = component.processing;
      }
    } else {
      isProcessing.value = false;
      if (stopWatcher) {
        stopWatcher();
        stopWatcher = null;
      }
    }
  } else {
    isProcessing.value = false;
    if (stopWatcher) {
      stopWatcher();
      stopWatcher = null;
    }
  }
});

// 监听路由变化，重置处理状态
watch(() => route.name, () => {
  isProcessing.value = false;
  // 清理之前的 watcher
  if (stopWatcher) {
    stopWatcher();
    stopWatcher = null;
  }
});

onUnmounted(() => {
  if (stopWatcher) {
    stopWatcher();
  }
});
</script>

<style scoped>
/* 基础变量 */
.image-processor {
  --primary-color: #6366f1;
  --primary-light: #818cf8;
  --primary-dark: #4f46e5;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
  --bg-dark: #0f172a;
  --bg-card: #1e293b;
  --bg-card-hover: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --border-color: #334155;
  --shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.3);

  height: 100vh;
  background: linear-gradient(135deg, var(--bg-dark) 0%, #1a1a2e 50%, #16213e 100%);
  color: var(--text-primary);
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* 顶部标题栏 */
.app-header {
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.logo-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.logo-section h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  background: linear-gradient(90deg, var(--text-primary), var(--primary-light));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 只隐藏主 tabs 的内容，不影响子组件中的 tabs */
.image-processor > .el-tabs :deep(.el-tabs__content) {
  padding: 2px;
  display: none !important; /* 隐藏默认的 tab-pane 内容，因为我们使用 router-view */
}

/* 确保子组件中的 tabs 内容正常显示 */
.image-processor .router-view-container :deep(.el-tabs__content) {
  display: block !important;
}

/* 路由视图容器 */
.router-view-container {
  /* padding: 20px; */
  /* min-height: calc(100vh - 120px); */
  background-color: #fff;
}



/* 处理状态指示器 */
.processing-indicator {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: var(--bg-card);
  border: 1px solid var(--primary-color);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  z-index: 1000;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
