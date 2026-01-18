
/**
 * 主进程与渲染进程通信频道定义
 * Definition of communication channels between main process and rendering process
 */
const ipcApiRoute = {
  test: 'controller/example/test',
  获取设备列表: 'controller/example/获取设备列表',
  开始任务: 'controller/example/开始任务',
  结束任务: 'controller/example/结束任务',
  sendToPython: 'controller/example/sendToPython',
  handleImageClick: 'controller/example/handleImageClick',
  openSaveDialog: 'controller/example/openSaveDialog',
  saveBase64Image: 'controller/example/saveBase64Image',
  openDirectoryDialog: 'controller/example/openDirectoryDialog',
  openFileDialog: 'controller/example/openFileDialog',
  // 截图功能
  openCaptureWindow: 'controller/example/openCaptureWindow',
  closeCaptureWindow: 'controller/example/closeCaptureWindow',
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
}

export {
  ipcApiRoute
}

