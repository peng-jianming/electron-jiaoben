'use strict';
const WebSocket = require('ws');
const { logger } = require('ee-core/log');
const path = require('path')
const { getSocketServer } = require('ee-core/socket');
const { getBaseDir, getExtraResourcesDir } = require('ee-core/ps');
const fs = require('fs');
const tkill = require('tree-kill');
const crossSpawn = require('cross-spawn');
const { BrowserWindow, screen, desktopCapturer } = require('electron');

class ExampleService {
  constructor() {
    // 存储结果窗口实例
    this.resultWindow = null;
    // 存储透明截图窗口实例
    this.captureWindow = null;
    // 存储截图预览窗口实例
    this.screenshotPreviewWindow = null;
    // 截图定时器
    this.captureTimer = null;
    // 截图状态
    this.isCapturing = false;
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

  /**
   * 创建透明截图区域窗口
   * @returns {Object} 窗口信息
   */
  createCaptureWindow() {
    // 如果窗口已存在，直接聚焦
    if (this.captureWindow && !this.captureWindow.isDestroyed()) {
      this.captureWindow.focus();
      return { success: true, message: '窗口已存在', windowId: this.captureWindow.id };
    }

    // 获取主显示器尺寸
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;

    // 创建透明窗口
    this.captureWindow = new BrowserWindow({
      width: 400,
      height: 300,
      x: Math.floor((width - 400) / 2),
      y: Math.floor((height - 300) / 2),
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: true,
      movable: true,
      hasShadow: false,
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
      },
    });

    // 加载透明窗口的 HTML 内容
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          html, body { 
            width: 100%; 
            height: 100%; 
            background: transparent;
            overflow: hidden;
          }
          .capture-area {
            width: 100%;
            height: 100%;
            border: 3px dashed #ff4757;
            background: rgba(255, 71, 87, 0.05);
            position: relative;
            cursor: move;
            -webkit-app-region: drag;
          }
          .resize-handle {
            position: absolute;
            background: #ff4757;
            -webkit-app-region: no-drag;
          }
          .resize-handle.corner {
            width: 12px;
            height: 12px;
            border-radius: 2px;
          }
          .resize-handle.se { bottom: 0; right: 0; cursor: se-resize; }
          .resize-handle.sw { bottom: 0; left: 0; cursor: sw-resize; }
          .resize-handle.ne { top: 0; right: 0; cursor: ne-resize; }
          .resize-handle.nw { top: 0; left: 0; cursor: nw-resize; }
          .close-btn {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 24px;
            height: 24px;
            background: #ff4757;
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            -webkit-app-region: no-drag;
            transition: transform 0.2s;
          }
          .close-btn:hover {
            transform: scale(1.1);
            background: #ff2f45;
          }
          .info-label {
            position: absolute;
            bottom: 8px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-family: 'Segoe UI', sans-serif;
            -webkit-app-region: no-drag;
            white-space: nowrap;
          }
        </style>
      </head>
      <body>
        <div class="capture-area">
          <button class="close-btn" onclick="window.close()">×</button>
          <div class="resize-handle corner se"></div>
          <div class="resize-handle corner sw"></div>
          <div class="resize-handle corner ne"></div>
          <div class="resize-handle corner nw"></div>
          <div class="info-label">拖动移动 | 角落调整大小</div>
        </div>
      </body>
      </html>
    `;

    this.captureWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`);

    // 窗口关闭时清理引用
    this.captureWindow.on('closed', () => {
      this.captureWindow = null;
      // 停止截图
      this.stopCapturing();
    });

    return { success: true, message: '截图窗口已创建', windowId: this.captureWindow.id };
  }

  /**
   * 关闭透明截图窗口
   */
  closeCaptureWindow() {
    if (this.captureWindow && !this.captureWindow.isDestroyed()) {
      this.captureWindow.close();
      this.captureWindow = null;
    }
    this.stopCapturing();
    return { success: true, message: '窗口已关闭' };
  }

  /**
   * 获取透明窗口的位置和大小
   */
  getCaptureWindowBounds() {
    if (!this.captureWindow || this.captureWindow.isDestroyed()) {
      return null;
    }
    return this.captureWindow.getBounds();
  }

  /**
   * 创建截图预览窗口
   */
  createScreenshotPreviewWindow() {
    const { getMainWindow } = require('ee-core/electron');
    const { getConfig } = require('ee-core/config');

    // 如果窗口已存在，直接聚焦
    if (this.screenshotPreviewWindow && !this.screenshotPreviewWindow.isDestroyed()) {
      this.screenshotPreviewWindow.focus();
      return { success: true, message: '预览窗口已存在' };
    }

    // 获取主窗口 URL 以确定加载地址
    const mainWindow = getMainWindow();
    let targetUrl = '';

    if (mainWindow && !mainWindow.isDestroyed()) {
      const mainUrl = mainWindow.webContents.getURL();
      if (mainUrl.includes('localhost') || mainUrl.includes('127.0.0.1')) {
        const urlMatch = mainUrl.match(/^(https?:\/\/[^\/]+)/);
        if (urlMatch) {
          targetUrl = `${urlMatch[1]}/#/screenshot-preview`;
        } else {
          targetUrl = 'http://localhost:8080/#/screenshot-preview';
        }
      } else {
        const config = getConfig();
        const indexPath = config.mainServer?.indexPath || '/public/dist/index.html';
        const indexPathFull = path.join(getBaseDir(), indexPath.replace(/^\//, ''));
        targetUrl = `file://${indexPathFull}#/screenshot-preview`;
      }
    } else {
      const config = getConfig();
      const isDev = process.env.NODE_ENV === 'development' || !config.mainServer;
      targetUrl = isDev 
        ? 'http://localhost:8080/#/screenshot-preview'
        : `file://${path.join(getBaseDir(), config.mainServer?.indexPath?.replace(/^\//, '') || 'public/dist/index.html')}#/screenshot-preview`;
    }

    // 创建预览窗口
    this.screenshotPreviewWindow = new BrowserWindow({
      width: 500,
      height: 400,
      minWidth: 300,
      minHeight: 200,
      title: '截图预览',
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
      },
      backgroundColor: '#1e1e1e',
      show: false,
    });

    this.screenshotPreviewWindow.loadURL(targetUrl);

    this.screenshotPreviewWindow.webContents.once('did-finish-load', () => {
      this.screenshotPreviewWindow.show();
      this.screenshotPreviewWindow.focus();
    });

    this.screenshotPreviewWindow.on('closed', () => {
      this.screenshotPreviewWindow = null;
    });

    return { success: true, message: '预览窗口已创建' };
  }

  /**
   * 开始连续截图
   */
  async startCapturing() {
    if (this.isCapturing) {
      return { success: false, message: '截图已在进行中' };
    }

    if (!this.captureWindow || this.captureWindow.isDestroyed()) {
      return { success: false, message: '请先打开截图窗口' };
    }

    // 创建预览窗口
    this.createScreenshotPreviewWindow();

    this.isCapturing = true;

    // 每秒截图
    this.captureTimer = setInterval(async () => {
      await this.captureScreen();
    }, 1000);

    // 立即执行一次
    await this.captureScreen();

    return { success: true, message: '开始截图' };
  }

  /**
   * 停止连续截图
   */
  stopCapturing() {
    if (this.captureTimer) {
      clearInterval(this.captureTimer);
      this.captureTimer = null;
    }
    this.isCapturing = false;
    return { success: true, message: '停止截图' };
  }

  /**
   * 获取截图状态
   */
  getCaptureStatus() {
    return {
      isCapturing: this.isCapturing,
      hasCaptureWindow: this.captureWindow && !this.captureWindow.isDestroyed(),
      hasPreviewWindow: this.screenshotPreviewWindow && !this.screenshotPreviewWindow.isDestroyed()
    };
  }

  /**
   * 执行一次屏幕截图
   */
  async captureScreen() {
    if (!this.captureWindow || this.captureWindow.isDestroyed()) {
      this.stopCapturing();
      return;
    }

    try {
      // 获取截图窗口的位置和大小
      const bounds = this.captureWindow.getBounds();
      
      // 边框宽度 (对应 CSS 中的 border: 3px)
      const borderWidth = 3;

      // 隐藏透明窗口中的控制元素（关闭按钮、角落手柄、提示标签）
      await this.captureWindow.webContents.executeJavaScript(`
        document.querySelectorAll('.close-btn, .resize-handle, .info-label').forEach(el => {
          el.style.visibility = 'hidden';
        });
      `);

      // 短暂延迟确保 UI 更新完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 获取所有可用的源
      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: {
          width: screen.getPrimaryDisplay().size.width,
          height: screen.getPrimaryDisplay().size.height
        }
      });

      // 恢复显示控制元素
      await this.captureWindow.webContents.executeJavaScript(`
        document.querySelectorAll('.close-btn, .resize-handle, .info-label').forEach(el => {
          el.style.visibility = 'visible';
        });
      `);

      if (sources.length === 0) {
        console.error('没有可用的屏幕源');
        return;
      }

      // 获取主屏幕的缩略图
      const source = sources[0];
      const thumbnail = source.thumbnail;

      // 裁剪到截图区域（排除边框区域）
      const cropX = bounds.x + borderWidth;
      const cropY = bounds.y + borderWidth;
      const cropWidth = Math.max(1, bounds.width - borderWidth * 2);
      const cropHeight = Math.max(1, bounds.height - borderWidth * 2);

      const croppedImage = thumbnail.crop({
        x: cropX,
        y: cropY,
        width: cropWidth,
        height: cropHeight
      });

      // 转换为 base64
      const base64Image = croppedImage.toDataURL();

      // 发送到预览窗口
      const socketServer = getSocketServer();
      if (socketServer) {
        socketServer.io.emit('screenshot-update', {
          image: base64Image,
          bounds: {
            x: cropX,
            y: cropY,
            width: cropWidth,
            height: cropHeight
          },
          timestamp: Date.now()
        });
      }

    } catch (error) {
      console.error('截图错误:', error);
      // 确保即使出错也恢复控制元素显示
      try {
        if (this.captureWindow && !this.captureWindow.isDestroyed()) {
          await this.captureWindow.webContents.executeJavaScript(`
            document.querySelectorAll('.close-btn, .resize-handle, .info-label').forEach(el => {
              el.style.visibility = 'visible';
            });
          `);
        }
      } catch (e) {}
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