'use strict';

const { exampleService } = require('../service/example');
const { getSocketServer } = require('ee-core/socket');
/**
 * example
 * @class
 */
class ExampleController {
  changeProp(args, event){
    console.log(args, "9999999");
    
    // exampleService.changeDeviceProcesses(args.deviceId, args.prop, args.message)
  }

  /**
   * 接收 Python 处理后的图像结果
   * @param {Object} args - 参数对象
   * @param {Object} event - 事件对象
   */
  receiveProcessedImage(args, event) {
    try {
      const imageData = args.message;
      
      // 只要有图像数据（原图或处理后的图像），就在新窗口中显示
      if (imageData && imageData.success && (imageData.processedImage || imageData.originalImage)) {
        exampleService.showImageResultWindow(imageData);
      }
      
      // 同时向前端发送处理结果（保持原有功能）
      const socketServer = getSocketServer();
      if (socketServer) {
        socketServer.io.emit('image-processed', imageData);
      }
      
      return { success: true, message: '处理结果已发送' };
    } catch (error) {
      console.error('发送处理结果错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 发送消息到 Python 客户端
   * @param {Object} args - 参数对象
   * @param {Object} event - 事件对象
   */
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

  /**
   * 处理图片点击事件（从图片显示窗口发送）
   * @param {Object} args - 参数对象 {x, y}
   * @param {Object} event - 事件对象
   */
  handleImageClick(args, event) {
    try {
      const { exampleService } = require('../service/example');
      const { getMainWindow } = require('ee-core/electron');
      
      // 转发到主窗口
      const mainWindow = getMainWindow();
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('image-click', args);
      }
      
      return { success: true, message: '图片点击事件已转发' };
    } catch (error) {
      console.error('转发图片点击事件错误:', error);
      return { success: false, message: error.message };
    }
  }
}
ExampleController.toString = () => '[class ExampleController]';

module.exports = ExampleController; 