'use strict';

const { exampleService } = require('../service/example');
const { getSocketServer } = require('ee-core/socket');
/**
 * example
 * @class
 */
class ExampleController {

  /**
   * 所有方法接收两个参数
   * @param args 前端传的参数
   * @param event - ipc通信时才有值。详情见：控制器文档
   */

  async 获取设备列表() {
   const list =  await exampleService.获取设备列表();   
   return list;
  }

  async 开始任务(args, event) {
    const params = args || {};
    JSON.parse(params.deviceList || '[]').forEach(item => {
      this.sendToPython({
        type: 'start',
        device_id: item.deviceId,
        task_queue: ['zhuagui']
      });
    });
  }

  async 结束任务(args, event) {
    const params = args || {};
    JSON.parse(params.deviceList || '[]').forEach(item => {
      this.sendToPython({
        type: 'stop',
        device_id: item.deviceId
      });
    });
  }
  changeProp(args, event){
    exampleService.changeDeviceProcesses(args.deviceId, args.prop, args.message)
  }

  sendToPython(args, event) {
    try {
      // 获取 socket 服务器实例
      const socketServer = getSocketServer();
      
      if (!socketServer) {
        console.error('Socket 服务器未初始化');
        return { success: false, message: 'Socket 服务器未初始化' };
      }

      // 向所有连接的客户端发送消息
      // 事件名：'python-message'
      // 数据：args 对象
      socketServer.io.emit('python-message', args);
      
      return { success: true, message: '消息已发送' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }
}
ExampleController.toString = () => '[class ExampleController]';

module.exports = ExampleController; 