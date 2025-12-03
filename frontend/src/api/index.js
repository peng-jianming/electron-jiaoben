
/**
 * 主进程与渲染进程通信频道定义
 * Definition of communication channels between main process and rendering process
 */
const ipcApiRoute = {
  test: 'controller/example/test',
  获取设备列表: 'controller/example/获取设备列表',
  开始任务: 'controller/example/开始任务',
  结束任务: 'controller/example/结束任务',
}

export {
  ipcApiRoute
}

