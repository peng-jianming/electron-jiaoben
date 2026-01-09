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
      
      // 设备列表事件
      if (prop === 'device-list') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('device-list', imageData);
        }
        return { success: true, message: '设备列表已发送' };
      }

      // 设备选择事件
      if (prop === 'device-selected') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('device-selected', imageData);
        }
        return { success: true, message: '设备选择结果已发送' };
      }

      // 设备截图事件
      if (prop === 'device-screenshot') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('device-screenshot', imageData);
        }
        return { success: true, message: '设备截图已发送' };
      }
      
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
   * 保存 base64 图片到文件
   * @param {Object} args - 参数对象 { filePath, imageData }
   * @param {Object} event - 事件对象
   */
  async saveBase64Image(args, event) {
    try {
      const fs = require('fs');
      const path = require('path');

      const { filePath, imageData } = args;
      if (!filePath || !imageData) {
        return { success: false, error: '缺少必要参数' };
      }

      // 确保目录存在
      const saveDir = path.dirname(filePath);
      if (saveDir && !fs.existsSync(saveDir)) {
        fs.mkdirSync(saveDir, { recursive: true });
      }

      // 将 base64 转换为 Buffer 并写入文件
      const buffer = Buffer.from(imageData, 'base64');
      fs.writeFileSync(filePath, buffer);

      return { success: true, path: filePath };
    } catch (error) {
      console.error('保存图片错误:', error);
      return { success: false, error: error.message };
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

  // ==================== 路径规划功能 ====================

  /**
   * 载入路径规划地图
   */
  async loadPathfindingMap(args, event) {
    try {
      return await exampleService.loadPathfindingMap();
    } catch (error) {
      console.error('载入地图错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 设置起点
   */
  setStartPoint(args, event) {
    try {
      return exampleService.setStartPoint(args);
    } catch (error) {
      console.error('设置起点错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 设置终点
   */
  setEndPoint(args, event) {
    try {
      return exampleService.setEndPoint(args);
    } catch (error) {
      console.error('设置终点错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 设置选点模式
   */
  setSelectPointMode(args, event) {
    try {
      return exampleService.setSelectPointMode(args.type);
    } catch (error) {
      console.error('设置选点模式错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 处理地图点击事件
   */
  handleMapPointClick(args, event) {
    try {
      return exampleService.handleMapPointClick(args);
    } catch (error) {
      console.error('处理地图点击错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 路径规划
   */
  planPath(args, event) {
    try {
      // 确保参数是纯对象
      const start = { x: Number(args.start.x), y: Number(args.start.y) };
      const end = { x: Number(args.end.x), y: Number(args.end.y) };
      const result = exampleService.planPath(start, end);
      // 确保返回值可序列化
      return JSON.parse(JSON.stringify(result));
    } catch (error) {
      console.error('路径规划错误:', error);
      return { success: false, message: String(error.message || error) };
    }
  }

  /**
   * 清除路径
   */
  clearPath(args, event) {
    try {
      return exampleService.clearPath();
    } catch (error) {
      console.error('清除路径错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 获取路径规划状态
   */
  getPathfindingStatus(args, event) {
    try {
      return exampleService.getPathfindingStatus();
    } catch (error) {
      console.error('获取路径规划状态错误:', error);
      return { success: false, message: error.message };
    }
  }
}
ExampleController.toString = () => '[class ExampleController]';

module.exports = ExampleController; 