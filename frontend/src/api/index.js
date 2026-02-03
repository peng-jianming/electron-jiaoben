
/**
 * 主进程与渲染进程通信频道定义
 * Definition of communication channels between main process and rendering process
 */
const ipcApiRoute = {
  获取账号列表: 'controller/example/获取账号列表',
  保存账号列表: 'controller/example/保存账号列表',
  发送到后端: 'controller/example/发送到后端',
}

export {
  ipcApiRoute
}

