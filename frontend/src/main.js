import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import './assets/global.less';
import components from './components/global';
import Router from './router/index';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import { initMatchSocket, getMatchSocket } from '@/utils/matchSocket';
import { ipc } from '@/utils/ipcRenderer';
import { ipcApiRoute } from '@/api';

const app = createApp(App);
const pinia = createPinia();

// components
for (const i in components) {
  app.component(i, components[i]);
}

app.use(pinia);
app.use(ElementPlus);

initMatchSocket().then(() => {
  const socket = getMatchSocket();
  window.matchSocket = socket;
  app.config.globalProperties.$matchSocket = socket;

  // 连接成功后，通知 electron 启动后端服务
  ipc.invoke(ipcApiRoute.启动后端服务);

  app.use(Router).mount('#app');
});
