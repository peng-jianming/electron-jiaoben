'use strict';
const WebSocket = require('ws');
const { logger } = require('ee-core/log');
const path = require('path')
const { getSocketServer } = require('ee-core/socket');
const { getBaseDir, getExtraResourcesDir } = require('ee-core/ps');
const fs = require('fs');
const tkill = require('tree-kill');
const crossSpawn = require('cross-spawn');
const { BrowserWindow, screen, desktopCapturer, dialog } = require('electron');
const { getDataDir } = require('ee-core/ps');
const _ = require('lodash');

class ExampleService {
  constructor() {
    // 存储透明截图窗口实例
    this.captureWindow = null;
    // 存储截图预览窗口实例
    this.screenshotPreviewWindow = null;
    // 截图定时器
    this.captureTimer = null;
    // 截图状态
    this.isCapturing = false;
    
    // JSON 文件存储路径
    const dataDir = getDataDir();
    this.configFilePath = path.join(dataDir, 'codeGenerator.json');
    
    // 确保目录存在
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }
    
    // 初始化配置文件（如果不存在）
    if (!fs.existsSync(this.configFilePath)) {
      fs.writeFileSync(this.configFilePath, JSON.stringify({ paths: {} }, null, 2), 'utf8');
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

  /**
   * 执行一次截屏窗口区域截图并返回 base64 给调用方（供主进程 IPC 返回给渲染进程）
   * @returns {Promise<{ success: boolean, image?: string, message?: string }>}
   */
  async captureScreenOnce() {
    if (!this.captureWindow || this.captureWindow.isDestroyed()) {
      return { success: false, message: '请先打开截屏窗口' };
    }

    try {
      const bounds = this.captureWindow.getBounds();
      const borderWidth = 3;

      await this.captureWindow.webContents.executeJavaScript(`
        document.querySelectorAll('.close-btn, .resize-handle, .info-label').forEach(el => {
          el.style.visibility = 'hidden';
        });
      `);
      await new Promise(resolve => setTimeout(resolve, 50));

      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: {
          width: screen.getPrimaryDisplay().size.width,
          height: screen.getPrimaryDisplay().size.height
        }
      });

      await this.captureWindow.webContents.executeJavaScript(`
        document.querySelectorAll('.close-btn, .resize-handle, .info-label').forEach(el => {
          el.style.visibility = 'visible';
        });
      `);

      if (sources.length === 0) {
        return { success: false, message: '没有可用的屏幕源' };
      }

      const source = sources[0];
      const thumbnail = source.thumbnail;
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
      const base64Image = croppedImage.toDataURL();
      return { success: true, image: base64Image };
    } catch (error) {
      console.error('截屏窗口截图错误:', error);
      try {
        if (this.captureWindow && !this.captureWindow.isDestroyed()) {
          await this.captureWindow.webContents.executeJavaScript(`
            document.querySelectorAll('.close-btn, .resize-handle, .info-label').forEach(el => {
              el.style.visibility = 'visible';
            });
          `);
        }
      } catch (e) {}
      return { success: false, message: error.message || '截图失败' };
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

  // ==================== 路径配置存储功能 ====================

  /**
   * 保存路径配置
   * @param {Object} paths - 路径对象 { resourcePath, configPath, fontLibraryPath }
   */
  savePaths(paths) {
    try {
      // 读取现有配置
      let config = {};
      if (fs.existsSync(this.configFilePath)) {
        const content = fs.readFileSync(this.configFilePath, 'utf8');
        config = JSON.parse(content);
      }
      
      // 更新路径配置
      if (!config.paths) {
        config.paths = {};
      }
      Object.assign(config.paths, paths);
      
      // 保存到文件
      fs.writeFileSync(this.configFilePath, JSON.stringify(config, null, 2), 'utf8');
      
      return { success: true, data: config.paths };
    } catch (error) {
      console.error('保存路径配置错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 读取路径配置
   */
  getPaths() {
    try {
      const defaultPaths = { resourcePath: '', configPath: '', fontLibraryPath: '', imageLibraryPath: '' };
      if (!fs.existsSync(this.configFilePath)) {
        return { success: true, data: defaultPaths };
      }

      const content = fs.readFileSync(this.configFilePath, 'utf8');
      const config = JSON.parse(content);

      const paths = config.paths || {};

      if (_.isEmpty(paths)) {
        return { success: true, data: defaultPaths };
      }

      return { success: true, data: { ...defaultPaths, ...paths } };
    } catch (error) {
      console.error('读取路径配置错误:', error);
      return { success: false, message: error.message, data: { resourcePath: '', configPath: '', fontLibraryPath: '', imageLibraryPath: '' } };
    }
  }
}
ExampleService.toString = () => '[class ExampleService]';

// 创建单例实例
const exampleService = new ExampleService();

module.exports = {
  ExampleService,
  exampleService
};