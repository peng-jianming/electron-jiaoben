'use strict';

const { exampleService } = require('../service/example');
const { getSocketServer } = require('ee-core/socket');
const { dialog, shell } = require('electron');
const {
  getMainWindow
} = require('ee-core/electron/window');
const fs = require('fs');
const path = require('path');
/**
 * example
 * @class
 */
class ExampleController {
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

      // 图片匹配结果事件
      if (prop === 'image-match-result') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('image-match-result', imageData);
        }
        return { success: true, message: '图片匹配结果已发送' };
      }

      // 字库匹配结果事件
      if (prop === 'font-library-match-result') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('font-library-match-result', imageData);
        }
        return { success: true, message: '字库匹配结果已发送' };
      }

      // 字库识字结果事件
      if (prop === 'font-library-ocr-result') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('font-library-ocr-result', imageData);
        }
        return { success: true, message: '字库识字结果已发送' };
      }

      // 拼接结果事件
      if (prop === 'stitch-result') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('stitch-result', imageData);
        }
        return { success: true, message: '拼接结果已发送' };
      }

      // 存储图片查询结果
      if (prop === 'stored-image-result') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('stored-image-result', imageData);
        }
        return { success: true, message: '存储图片结果已发送' };
      }

      // 图片库加载结果事件
      if (prop === 'image-library') {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('image-library', imageData);
        }
        return { success: true, message: '图片库结果已发送' };
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
   * 打开文件夹选择对话框
   * @param {Object} args - 参数对象
   * @param {Object} event - 事件对象
   */
  async openDirectoryDialog(args, event) {
    try {
      const { getMainWindow } = require('ee-core/electron');
      const mainWindow = getMainWindow();
      
      const result = await dialog.showOpenDialog(mainWindow, {
        title: args.title || '选择文件夹',
        defaultPath: args.defaultPath || '',
        properties: ['openDirectory']
      });
      
      if (result.canceled || result.filePaths.length === 0) {
        return { success: false, canceled: true };
      }
      
      return { success: true, filePath: result.filePaths[0] };
    } catch (error) {
      console.error('打开文件夹选择对话框错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 打开文件选择对话框
   * @param {Object} args - 参数对象
   * @param {Object} event - 事件对象
   */
  async openFileDialog(args, event) {
    try {
      const { getMainWindow } = require('ee-core/electron');
      const mainWindow = getMainWindow();
      
      const result = await dialog.showOpenDialog(mainWindow, {
        title: args.title || '选择文件',
        defaultPath: args.defaultPath || '',
        filters: args.filters || [
          { name: '所有文件', extensions: ['*'] }
        ],
        properties: ['openFile']
      });
      
      if (result.canceled || result.filePaths.length === 0) {
        return { success: false, canceled: true };
      }
      
      return { success: true, filePath: result.filePaths[0] };
    } catch (error) {
      console.error('打开文件选择对话框错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 读取文本文件内容
   * @param {Object} args - 参数对象 { filePath: string }
   * @param {Object} event - 事件对象
   */
  readTextFile(args, event) {
    try {
      if (!args || !args.filePath) {
        return { success: false, message: '文件路径不能为空' };
      }

      const filePath = args.filePath;
      
      // 检查文件是否存在
      if (!fs.existsSync(filePath)) {
        return { success: false, message: '文件不存在' };
      }

      // 读取文件内容
      const content = fs.readFileSync(filePath, 'utf8');
      const fileName = path.basename(filePath);

      return {
        success: true,
        content: content,
        fileName: fileName,
        filePath: filePath
      };
    } catch (error) {
      console.error('读取文件错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 写入文本文件内容
   * @param {Object} args - 参数对象 { filePath: string, content: string }
   * @param {Object} event - 事件对象
   */
  writeTextFile(args, event) {
    try {
      if (!args || !args.filePath) {
        return { success: false, message: '文件路径不能为空' };
      }

      if (args.content === undefined || args.content === null) {
        return { success: false, message: '文件内容不能为空' };
      }

      const filePath = args.filePath;
      
      // 写入文件内容
      fs.writeFileSync(filePath, args.content, 'utf8');

      return {
        success: true,
        filePath: filePath
      };
    } catch (error) {
      console.error('写入文件错误:', error);
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
   * 执行一次截屏窗口区域截图并返回 base64 给渲染进程
   */
  async captureScreenOnce(args, event) {
    try {
      return await exampleService.captureScreenOnce();
    } catch (error) {
      console.error('截屏窗口截图错误:', error);
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

  // ==================== 路径配置存储功能 ====================

  /**
   * 保存路径配置（只更新传入的字段，未传入的路径不会被清除）
   * @param {Object} args - 参数对象，可包含 resourcePath, configPath, fontLibraryPath, imageLibraryPath 的任意子集
   */
  savePaths(args, event) {
    try {
      const toSave = {};
      if (args.hasOwnProperty('resourcePath')) toSave.resourcePath = args.resourcePath || '';
      if (args.hasOwnProperty('configPath')) toSave.configPath = args.configPath || '';
      if (args.hasOwnProperty('fontLibraryPath')) toSave.fontLibraryPath = args.fontLibraryPath || '';
      if (args.hasOwnProperty('imageLibraryPath')) toSave.imageLibraryPath = args.imageLibraryPath || '';
      return exampleService.savePaths(toSave);
    } catch (error) {
      console.error('保存路径配置错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 读取路径配置
   */
  getPaths(args, event) {
    try {
      return exampleService.getPaths();
    } catch (error) {
      console.error('读取路径配置错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 使用系统默认程序打开文件
   * @param {Object} args - 参数对象 { filePath: string }
   * @param {Object} event - 事件对象
   */
  async openFile(args, event) {
    try {
      if (!args || !args.filePath) {
        return { success: false, message: '文件路径不能为空' };
      }

      const filePath = args.filePath;
      
      // 检查文件是否存在
      if (!fs.existsSync(filePath)) {
        return { success: false, message: '文件不存在' };
      }

      // 使用系统默认程序打开文件
      await shell.openPath(filePath);

      return { success: true, message: '文件已打开' };
    } catch (error) {
      console.error('打开文件错误:', error);
      return { success: false, message: error.message };
    }
  }

  操作主窗口(args, event) {
    const win = getMainWindow();
    if (!win || win.isDestroyed()) return;
    const fn = win[args.操作方法];
    if (typeof fn === 'function') {
      fn.apply(win, args.操作参数 != null ? (Array.isArray(args.操作参数) ? args.操作参数 : [args.操作参数]) : []);
    }
  }

  /** 获取主窗口位置，用于标题栏拖动 */
  获取主窗口位置(args, event) {
    const win = getMainWindow();
    if (!win || win.isDestroyed()) return { x: 0, y: 0 };
    const [x, y] = win.getPosition();
    return { x, y };
  }

  /** 设置主窗口位置，用于标题栏拖动 */
  设置主窗口位置(args, event) {
    const win = getMainWindow();
    if (!win || win.isDestroyed()) return;
    const { x, y } = args;
    if (typeof x === 'number' && typeof y === 'number') {
      win.setPosition(Math.round(x), Math.round(y));
    }
  }
}
ExampleController.toString = () => '[class ExampleController]';

module.exports = ExampleController; 