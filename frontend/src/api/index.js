
/**
 * 主进程与渲染进程通信频道定义
 * Definition of communication channels between main process and rendering process
 */
const ipcApiRoute = {
  操作主窗口: 'controller/example/操作主窗口',
  获取主窗口位置: 'controller/example/获取主窗口位置',
  设置主窗口位置: 'controller/example/设置主窗口位置',

  获取设备列表: 'controller/example/获取设备列表',
  开始任务: 'controller/example/开始任务',
  结束任务: 'controller/example/结束任务',
  sendToPython: 'controller/example/sendToPython',
  openSaveDialog: 'controller/example/openSaveDialog',
  saveBase64Image: 'controller/example/saveBase64Image',
  openDirectoryDialog: 'controller/example/openDirectoryDialog',
  openFileDialog: 'controller/example/openFileDialog',
  readTextFile: 'controller/example/readTextFile',
  writeTextFile: 'controller/example/writeTextFile',
  openFile: 'controller/example/openFile',
  // 截图功能
  openCaptureWindow: 'controller/example/openCaptureWindow',
  closeCaptureWindow: 'controller/example/closeCaptureWindow',
  captureScreenOnce: 'controller/example/captureScreenOnce',
  startCapturing: 'controller/example/startCapturing',
  stopCapturing: 'controller/example/stopCapturing',
  getCaptureStatus: 'controller/example/getCaptureStatus',
  // 路径规划功能
  loadPathfindingMap: 'controller/example/loadPathfindingMap',
  setStartPoint: 'controller/example/setStartPoint',
  setEndPoint: 'controller/example/setEndPoint',
  setSelectPointMode: 'controller/example/setSelectPointMode',
  planPath: 'controller/example/planPath',
  clearPath: 'controller/example/clearPath',
  getPathfindingStatus: 'controller/example/getPathfindingStatus',
  // 路径配置存储功能
  savePaths: 'controller/example/savePaths',
  getPaths: 'controller/example/getPaths',
}

export {
  ipcApiRoute
}

