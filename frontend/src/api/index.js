
/**
 * 主进程与渲染进程通信频道定义
 * Definition of communication channels between main process and rendering process
 */
const ipcApiRoute = {
  启动后端服务: 'controller/example/启动后端服务',
  发送到后端: 'controller/example/发送到后端',
  操作主窗口: 'controller/example/操作主窗口',
  获取主窗口位置: 'controller/example/获取主窗口位置',
  设置主窗口位置: 'controller/example/设置主窗口位置',
  打开小地图截屏框: 'controller/example/打开小地图截屏框',
  关闭小地图截屏框: 'controller/example/关闭小地图截屏框',
}

export {
  ipcApiRoute
}

