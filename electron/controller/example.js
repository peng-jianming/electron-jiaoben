'use strict';

const { exampleService } = require('../service/example');
const { getSocketServer } = require('ee-core/socket');
const { dialog } = require('electron');
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
      const prop = args.prop;
      const imageData = args.message;
      
      // 根据 prop 类型分发事件
      if (prop === 'image-saved') {
        // 保存结果事件
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('image-saved', imageData);
        }
        return { success: true, message: '保存结果已发送' };
      }
      
      // 图像处理结果事件 (image-processed)
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

  /**
   * 打开保存文件对话框
   * @param {Object} args - 参数对象
   * @param {Object} event - 事件对象
   */
  async openSaveDialog(args, event) {
    try {
      const { getMainWindow } = require('ee-core/electron');
      const mainWindow = getMainWindow();
      
      const result = await dialog.showSaveDialog(mainWindow, {
        title: '保存图片',
        defaultPath: args.defaultName || 'processed_image.png',
        filters: [
          { name: 'PNG 图片', extensions: ['png'] },
          { name: 'JPEG 图片', extensions: ['jpg', 'jpeg'] },
          { name: 'BMP 图片', extensions: ['bmp'] },
          { name: '所有文件', extensions: ['*'] }
        ]
      });
      
      if (result.canceled || !result.filePath) {
        return { success: false, canceled: true };
      }
      
      return { success: true, filePath: result.filePath };
    } catch (error) {
      console.error('打开保存对话框错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 打开截图窗口
   */
  openCaptureWindow(args, event) {
    try {
      return exampleService.createCaptureWindow();
    } catch (error) {
      console.error('打开截图窗口错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 关闭截图窗口
   */
  closeCaptureWindow(args, event) {
    try {
      return exampleService.closeCaptureWindow();
    } catch (error) {
      console.error('关闭截图窗口错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 开始连续截图
   */
  async startCapturing(args, event) {
    try {
      return await exampleService.startCapturing();
    } catch (error) {
      console.error('开始截图错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 停止连续截图
   */
  stopCapturing(args, event) {
    try {
      return exampleService.stopCapturing();
    } catch (error) {
      console.error('停止截图错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 获取截图状态
   */
  getCaptureStatus(args, event) {
    try {
      return exampleService.getCaptureStatus();
    } catch (error) {
      console.error('获取截图状态错误:', error);
      return { success: false, message: error.message };
    }
  }
}
ExampleController.toString = () => '[class ExampleController]';

module.exports = ExampleController; 