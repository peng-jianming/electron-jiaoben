
/**
 * 主进程与渲染进程通信频道定义
 * Definition of communication channels between main process and rendering process
 */
const ipcApiRoute = {
  获取账号列表: 'controller/example/获取账号列表',
  保存账号列表: 'controller/example/保存账号列表',
  获取任务配置: 'controller/example/获取任务配置',
  保存任务配置: 'controller/example/保存任务配置',
  发送到后端: 'controller/example/发送到后端',
  操作主窗口: 'controller/example/操作主窗口',
  获取主窗口位置: 'controller/example/获取主窗口位置',
  设置主窗口位置: 'controller/example/设置主窗口位置',
}

export {
  ipcApiRoute
}

