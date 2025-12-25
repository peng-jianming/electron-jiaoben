'use strict';
const WebSocket = require('ws');
const { logger } = require('ee-core/log');
const path = require('path')
const { getSocketServer } = require('ee-core/socket');
const { getBaseDir, getExtraResourcesDir } = require('ee-core/ps');
const fs = require('fs');
const tkill = require('tree-kill');
const crossSpawn = require('cross-spawn');
const { BrowserWindow } = require('electron');

class ExampleService {
  constructor() {
    // 存储结果窗口实例
    this.resultWindow = null;
  }

  /**
   * 创建或显示图像处理结果窗口
   * @param {Object} imageData - 图像数据对象
   * @param {string} imageData.processedImage - base64 编码的处理后图像
   * @param {number} imageData.threshold - 使用的阈值
   * @param {boolean} imageData.success - 是否成功
   * @param {string} imageData.error - 错误信息（如果有）
   */
  showImageResultWindow(imageData) {
    const { getMainWindow } = require('ee-core/electron');
    const { getConfig } = require('ee-core/config');
    
    // 如果窗口已存在，通过 Socket.IO 发送数据并聚焦窗口
    if (this.resultWindow && !this.resultWindow.isDestroyed()) {
      // 通过 Socket.IO 发送数据到新窗口
      const socketServer = getSocketServer();
      if (socketServer) {
        socketServer.io.emit('image-processed', imageData);
      }
      this.resultWindow.focus();
      return;
    }
    
    // 获取主窗口 URL 以确定加载地址
    const mainWindow = getMainWindow();
    let targetUrl = '';
    
    if (mainWindow && !mainWindow.isDestroyed()) {
      const mainUrl = mainWindow.webContents.getURL();
      // 如果是开发环境（localhost），使用开发服务器地址
      if (mainUrl.includes('localhost') || mainUrl.includes('127.0.0.1')) {
        // 从主窗口 URL 提取协议和主机
        const urlMatch = mainUrl.match(/^(https?:\/\/[^\/]+)/);
        if (urlMatch) {
          targetUrl = `${urlMatch[1]}/#/image-result`;
        } else {
          // 默认开发服务器地址
          targetUrl = 'http://localhost:8080/#/image-result';
        }
      } else {
        // 生产环境，使用文件路径
        const config = getConfig();
        const indexPath = config.mainServer?.indexPath || '/public/dist/index.html';
        const indexPathFull = path.join(getBaseDir(), indexPath.replace(/^\//, ''));
        targetUrl = `file://${indexPathFull}#/image-result`;
      }
    } else {
      // 如果无法获取主窗口，尝试使用配置
      const config = getConfig();
      const isDev = process.env.NODE_ENV === 'development' || !config.mainServer;
      targetUrl = isDev 
        ? 'http://localhost:8080/#/image-result'
        : `file://${path.join(getBaseDir(), config.mainServer?.indexPath?.replace(/^\//, '') || 'public/dist/index.html')}#/image-result`;
    }
    
    // 创建新窗口 - 设置较大的初始尺寸以适应大图片
    this.resultWindow = new BrowserWindow({
      width: 1200,
      height: 900,
      minWidth: 400,
      minHeight: 300,
      title: '图像处理结果',
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
      },
      backgroundColor: '#1e1e1e',
      show: false, // 先不显示，等加载完成后再显示
    });
    
    // 加载 Vue 路由
    this.resultWindow.loadURL(targetUrl);
    
    // 存储要显示的数据，等待窗口准备好
    const pendingData = imageData;
    
    // 窗口准备好后通过 Socket.IO 发送图像数据并显示
    this.resultWindow.webContents.once('did-finish-load', () => {
      // 延迟一下确保 Vue 应用和 Socket.IO 已初始化
      setTimeout(() => {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('image-processed', pendingData);
        }
        this.resultWindow.show();
        this.resultWindow.focus();
      }, 500);
    });
    
    // 窗口关闭时清理引用
    this.resultWindow.on('closed', () => {
      this.resultWindow = null;
    });
  }
  
  /**
   * 转发图片点击事件到主窗口
   * @param {Object} data - 点击位置数据 {x, y}
   */
  forwardImageClick(data) {
    const { getMainWindow } = require('ee-core/electron');
    const mainWindow = getMainWindow();
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('image-click', data);
    }
  }

  async createPythonServer(runPath, port) {
    return new Promise((resolve, reject) => {
    const coreProcess = crossSpawn('C:/ProgramData/anaconda3/python.exe', [ `python/index.py`], {
      stdio: ['inherit', 'inherit', 'inherit', 'ipc'],
      detached: false,
      cwd: runPath,
      maxBuffer: 1024 * 1024 * 1024,
      windowsHide: true
    });
    
      // 开启进程,记录进程id
      this.changeDeviceProcesses(port, 'pid', coreProcess.pid)

      coreProcess.on('exit', (code, signal) => {
        console.log('Python exit：', path, port, 'code=', code, 'signal=', signal);

        // 结束进程,删除进程id
        this.changeDeviceProcesses(port, 'pid', null)

        // 无论是否成功退出，都算本次任务结束，交由上层决定是否继续后续任务
        resolve({ code, signal });
      });

      coreProcess.on('error', (err) => {
        // 结束进程,删除进程id
        this.changeDeviceProcesses(port, 'pid', null)
        reject(err);
      });
    });
  }

  stopPythonServer(deviceId) {
    const current = this.deviceProcesses.get(deviceId)
    if (!current || !current.pid) return;
    tkill(current.pid, 'SIGINT', (err) => {
      if (err) {
        // 如果 SIGINT 失败，再尝试 SIGKILL，最终无论如何都认为结束
        tkill(current.pid, 'SIGKILL', () => { });
      }
    });
  }
}
ExampleService.toString = () => '[class ExampleService]';

// 创建单例实例
const exampleService = new ExampleService();

module.exports = {
  ExampleService,
  exampleService
};