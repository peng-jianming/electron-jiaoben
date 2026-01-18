'use strict';
const WebSocket = require('ws');
const { logger } = require('ee-core/log');
const path = require('path')
const { getSocketServer } = require('ee-core/socket');
const { getBaseDir, getExtraResourcesDir } = require('ee-core/ps');
const fs = require('fs');
const tkill = require('tree-kill');
const crossSpawn = require('cross-spawn');
const { BrowserWindow, screen, desktopCapturer, dialog, nativeImage } = require('electron');
const { getDataDir } = require('ee-core/ps');
const _ = require('lodash');

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
    // 路径规划地图窗口
    this.pathfindingMapWindow = null;
    // 地图数据
    this.mapData = null;
    this.mapWidth = 0;
    this.mapHeight = 0;
    this.mapFileName = '';
    // 起点终点
    this.startPoint = null;
    this.endPoint = null;
    // 路径
    this.currentPath = [];
    // 距离场（用于让路径走在中间）
    this.distanceField = null;
    
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

  // ==================== 路径规划功能 ====================

  /**
   * 载入路径规划地图
   */
  async loadPathfindingMap() {
    const { getMainWindow } = require('ee-core/electron');
    const mainWindow = getMainWindow();
    
    // 打开文件选择对话框
    const result = await dialog.showOpenDialog(mainWindow, {
      title: '选择二值化地图',
      filters: [
        { name: '图片文件', extensions: ['png', 'jpg', 'jpeg', 'bmp'] }
      ],
      properties: ['openFile']
    });
    
    if (result.canceled || result.filePaths.length === 0) {
      return { success: false, canceled: true };
    }
    
    const filePath = result.filePaths[0];
    this.mapFileName = path.basename(filePath);
    
    try {
      // 读取图片
      const image = nativeImage.createFromPath(filePath);
      const size = image.getSize();
      this.mapWidth = size.width;
      this.mapHeight = size.height;
      
      // 转换为 base64
      const base64 = image.toDataURL();
      this.mapData = base64;
      
      // 解析图片获取像素数据用于路径规划
      const bitmap = image.toBitmap();
      this.mapPixels = this.parseMapPixels(bitmap, size.width, size.height);
      
      // 计算距离场（用于让路径走在中间）
      this.distanceField = this.computeDistanceField();
      
      // 重置起点终点和路径
      this.startPoint = null;
      this.endPoint = null;
      this.currentPath = [];
      
      // 创建地图显示窗口
      this.createPathfindingMapWindow();
      
      // 发送地图数据到地图窗口
      setTimeout(() => {
        const socketServer = getSocketServer();
        if (socketServer) {
          socketServer.io.emit('map-data', {
            image: this.mapData,
            width: this.mapWidth,
            height: this.mapHeight,
            startPoint: this.startPoint,
            endPoint: this.endPoint
          });
        }
      }, 500);
      
      return {
        success: true,
        fileName: this.mapFileName,
        width: this.mapWidth,
        height: this.mapHeight
      };
    } catch (error) {
      console.error('加载地图错误:', error);
      return { success: false, message: error.message };
    }
  }

  /**
   * 解析地图像素数据
   * @param {Buffer} bitmap - 图片位图数据
   * @param {number} width - 宽度
   * @param {number} height - 高度
   * @returns {Array} 二维数组，0表示可通行，1表示障碍
   */
  parseMapPixels(bitmap, width, height) {
    const pixels = [];
    for (let y = 0; y < height; y++) {
      const row = [];
      for (let x = 0; x < width; x++) {
        // BGRA 格式
        const idx = (y * width + x) * 4;
        const b = bitmap[idx];
        const g = bitmap[idx + 1];
        const r = bitmap[idx + 2];
        // 计算灰度值，黑色(0)为障碍，白色(255)为可通行
        const gray = (r + g + b) / 3;
        // 阈值判断：灰度 < 128 为障碍(1)，否则为可通行(0)
        row.push(gray < 128 ? 1 : 0);
      }
      pixels.push(row);
    }
    return pixels;
  }

  /**
   * 计算距离场 - 每个可通行点到最近障碍物的距离
   * 使用 BFS 算法
   */
  computeDistanceField() {
    const width = this.mapWidth;
    const height = this.mapHeight;
    const grid = this.mapPixels;
    
    // 初始化距离场
    const distanceField = [];
    for (let y = 0; y < height; y++) {
      const row = [];
      for (let x = 0; x < width; x++) {
        // 障碍物距离为 0，可通行区域初始为无穷大
        row.push(grid[y][x] === 1 ? 0 : Infinity);
      }
      distanceField.push(row);
    }

    // BFS 队列，从所有障碍物开始
    const queue = [];
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (grid[y][x] === 1) {
          queue.push({ x, y, dist: 0 });
        }
      }
    }

    // 4方向扩展
    const directions = [
      { dx: 0, dy: -1 },
      { dx: 0, dy: 1 },
      { dx: -1, dy: 0 },
      { dx: 1, dy: 0 },
    ];

    // BFS 计算距离
    while (queue.length > 0) {
      const { x, y, dist } = queue.shift();
      
      for (const dir of directions) {
        const nx = x + dir.dx;
        const ny = y + dir.dy;
        
        if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
          const newDist = dist + 1;
          if (newDist < distanceField[ny][nx]) {
            distanceField[ny][nx] = newDist;
            queue.push({ x: nx, y: ny, dist: newDist });
          }
        }
      }
    }

    return distanceField;
  }

  /**
   * 创建路径规划地图窗口
   */
  createPathfindingMapWindow() {
    const { getMainWindow } = require('ee-core/electron');
    const { getConfig } = require('ee-core/config');

    // 如果窗口已存在，直接聚焦
    if (this.pathfindingMapWindow && !this.pathfindingMapWindow.isDestroyed()) {
      this.pathfindingMapWindow.focus();
      return { success: true, message: '窗口已存在' };
    }

    // 获取主窗口 URL 以确定加载地址
    const mainWindow = getMainWindow();
    let targetUrl = '';

    if (mainWindow && !mainWindow.isDestroyed()) {
      const mainUrl = mainWindow.webContents.getURL();
      if (mainUrl.includes('localhost') || mainUrl.includes('127.0.0.1')) {
        const urlMatch = mainUrl.match(/^(https?:\/\/[^\/]+)/);
        if (urlMatch) {
          targetUrl = `${urlMatch[1]}/#/pathfinding-map`;
        } else {
          targetUrl = 'http://localhost:8080/#/pathfinding-map';
        }
      } else {
        const config = getConfig();
        const indexPath = config.mainServer?.indexPath || '/public/dist/index.html';
        const indexPathFull = path.join(getBaseDir(), indexPath.replace(/^\//, ''));
        targetUrl = `file://${indexPathFull}#/pathfinding-map`;
      }
    } else {
      const config = getConfig();
      const isDev = process.env.NODE_ENV === 'development' || !config.mainServer;
      targetUrl = isDev 
        ? 'http://localhost:8080/#/pathfinding-map'
        : `file://${path.join(getBaseDir(), config.mainServer?.indexPath?.replace(/^\//, '') || 'public/dist/index.html')}#/pathfinding-map`;
    }

    // 创建窗口
    this.pathfindingMapWindow = new BrowserWindow({
      width: Math.min(this.mapWidth + 100, 1200),
      height: Math.min(this.mapHeight + 150, 900),
      minWidth: 400,
      minHeight: 300,
      title: '路径规划地图',
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
      },
      backgroundColor: '#1e1e1e',
      show: false,
    });

    this.pathfindingMapWindow.loadURL(targetUrl);

    this.pathfindingMapWindow.webContents.once('did-finish-load', () => {
      this.pathfindingMapWindow.show();
      this.pathfindingMapWindow.focus();
    });

    this.pathfindingMapWindow.on('closed', () => {
      this.pathfindingMapWindow = null;
      // 通知主窗口地图窗口已关闭
      const socketServer = getSocketServer();
      if (socketServer) {
        socketServer.io.emit('map-window-closed');
      }
    });

    return { success: true, message: '地图窗口已创建' };
  }

  /**
   * 设置起点
   */
  setStartPoint(point) {
    this.startPoint = point;
    const socketServer = getSocketServer();
    if (socketServer) {
      socketServer.io.emit('update-points', { startPoint: point });
    }
    return { success: true };
  }

  /**
   * 设置终点
   */
  setEndPoint(point) {
    this.endPoint = point;
    const socketServer = getSocketServer();
    if (socketServer) {
      socketServer.io.emit('update-points', { endPoint: point });
    }
    return { success: true };
  }

  /**
   * 设置选点模式（广播到地图窗口）
   */
  setSelectPointMode(type) {
    const socketServer = getSocketServer();
    if (socketServer) {
      socketServer.io.emit('select-point-mode', { type: type });
    }
    return { success: true };
  }

  /**
   * 处理地图点击事件（从地图窗口发送，广播到主窗口）
   */
  handleMapPointClick(data) {
    const socketServer = getSocketServer();
    if (socketServer) {
      socketServer.io.emit('map-point-clicked', data);
    }
    return { success: true };
  }

  /**
   * A* 路径规划算法
   */
  planPath(start, end) {
    if (!this.mapPixels || this.mapPixels.length === 0) {
      return { success: false, message: '请先载入地图' };
    }

    // 更新起点终点（确保是干净的副本）
    this.startPoint = { x: start.x, y: start.y };
    this.endPoint = { x: end.x, y: end.y };

    // 检查起点终点是否在地图范围内
    if (start.x < 0 || start.x >= this.mapWidth || start.y < 0 || start.y >= this.mapHeight) {
      return { success: false, message: '起点超出地图范围' };
    }
    if (end.x < 0 || end.x >= this.mapWidth || end.y < 0 || end.y >= this.mapHeight) {
      return { success: false, message: '终点超出地图范围' };
    }

    // 检查起点终点是否在障碍物上
    if (this.mapPixels[start.y][start.x] === 1) {
      return { success: false, message: '起点位于障碍物上' };
    }
    if (this.mapPixels[end.y][end.x] === 1) {
      return { success: false, message: '终点位于障碍物上' };
    }

    // A* 算法实现
    const path = this.astar(start, end);
    
    if (!path || path.length === 0) {
      return { success: false, message: '无法找到从起点到终点的路径' };
    }

    this.currentPath = path;

    // 发送路径到地图窗口
    const socketServer = getSocketServer();
    if (socketServer) {
      socketServer.io.emit('path-data', { path: path });
      socketServer.io.emit('update-points', { 
        startPoint: this.startPoint, 
        endPoint: this.endPoint 
      });
    }

    // 注意：不返回完整的 path 数组，因为可能太大导致 IPC 序列化失败
    // 路径已经通过 Socket.IO 发送到地图窗口了
    return { success: true, pathLength: path.length };
  }

  /**
   * A* 寻路算法实现（优化版：倾向于走在路的中间）
   */
  astar(start, end) {
    const width = this.mapWidth;
    const height = this.mapHeight;
    const grid = this.mapPixels;
    const distField = this.distanceField;

    // 计算最大距离值（用于归一化）
    let maxDist = 1;
    if (distField) {
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          if (distField[y][x] !== Infinity && distField[y][x] > maxDist) {
            maxDist = distField[y][x];
          }
        }
      }
    }

    // 贴边惩罚权重（值越大，越倾向于走中间）
    const wallPenaltyWeight = 3.0;

    // 启发函数：曼哈顿距离
    const heuristic = (a, b) => Math.abs(a.x - b.x) + Math.abs(a.y - b.y);

    // 计算贴边惩罚：距离障碍物越近，惩罚越大
    const getWallPenalty = (x, y) => {
      if (!distField) return 0;
      const dist = distField[y][x];
      if (dist === 0 || dist === Infinity) return 0;
      // 归一化后取反，距离越小惩罚越大
      // 使用指数函数使惩罚更明显
      const normalizedDist = dist / maxDist;
      return wallPenaltyWeight * (1 - normalizedDist) * (1 - normalizedDist);
    };

    // 8方向移动
    const directions = [
      { dx: 0, dy: -1 },  // 上
      { dx: 0, dy: 1 },   // 下
      { dx: -1, dy: 0 },  // 左
      { dx: 1, dy: 0 },   // 右
      { dx: -1, dy: -1 }, // 左上
      { dx: 1, dy: -1 },  // 右上
      { dx: -1, dy: 1 },  // 左下
      { dx: 1, dy: 1 },   // 右下
    ];

    // 开放列表和关闭列表
    const openSet = new Map();
    const closedSet = new Set();
    const cameFrom = new Map();
    const gScore = new Map();
    const fScore = new Map();

    const key = (p) => `${p.x},${p.y}`;

    // 初始化起点
    const startKey = key(start);
    openSet.set(startKey, start);
    gScore.set(startKey, 0);
    fScore.set(startKey, heuristic(start, end));

    while (openSet.size > 0) {
      // 找到 fScore 最小的节点
      let current = null;
      let currentKey = null;
      let minF = Infinity;
      
      for (const [k, node] of openSet) {
        const f = fScore.get(k) || Infinity;
        if (f < minF) {
          minF = f;
          current = node;
          currentKey = k;
        }
      }

      // 到达终点
      if (current.x === end.x && current.y === end.y) {
        // 重建路径
        const path = [];
        let curr = current;
        while (curr) {
          path.unshift({ x: curr.x, y: curr.y });
          curr = cameFrom.get(key(curr));
        }
        return path;
      }

      openSet.delete(currentKey);
      closedSet.add(currentKey);

      // 遍历邻居
      for (const dir of directions) {
        const nx = current.x + dir.dx;
        const ny = current.y + dir.dy;

        // 边界检查
        if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;

        // 障碍物检查
        if (grid[ny][nx] === 1) continue;

        const neighborKey = `${nx},${ny}`;

        // 已在关闭列表中
        if (closedSet.has(neighborKey)) continue;

        // 对角线移动时检查是否会穿过障碍物角落
        if (dir.dx !== 0 && dir.dy !== 0) {
          if (grid[current.y][nx] === 1 || grid[ny][current.x] === 1) continue;
        }

        // 计算 g 值（对角线移动代价为 1.414）
        const baseCost = (dir.dx !== 0 && dir.dy !== 0) ? 1.414 : 1;
        // 加入贴边惩罚
        const wallPenalty = getWallPenalty(nx, ny);
        const moveCost = baseCost + wallPenalty;
        const tentativeG = (gScore.get(currentKey) || 0) + moveCost;

        if (!openSet.has(neighborKey)) {
          openSet.set(neighborKey, { x: nx, y: ny });
        } else if (tentativeG >= (gScore.get(neighborKey) || Infinity)) {
          continue;
        }

        // 更新路径
        cameFrom.set(neighborKey, current);
        gScore.set(neighborKey, tentativeG);
        fScore.set(neighborKey, tentativeG + heuristic({ x: nx, y: ny }, end));
      }
    }

    // 无法找到路径
    return null;
  }

  /**
   * 清除路径
   */
  clearPath() {
    this.currentPath = [];
    const socketServer = getSocketServer();
    if (socketServer) {
      socketServer.io.emit('clear-path');
    }
    return { success: true };
  }

  /**
   * 获取路径规划状态
   */
  getPathfindingStatus() {
    return {
      hasMap: !!this.mapData,
      mapWidth: this.mapWidth,
      mapHeight: this.mapHeight,
      startPoint: this.startPoint,
      endPoint: this.endPoint,
      hasPath: this.currentPath.length > 0,
      pathLength: this.currentPath.length
    };
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
   * @param {Object} paths - 路径对象 { resourcePath, configPath }
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
      if (!fs.existsSync(this.configFilePath)) {
        return { success: true, data: { resourcePath: '', configPath: '' } };
      }
      
      const content = fs.readFileSync(this.configFilePath, 'utf8');
      const config = JSON.parse(content);
      
      const paths = config.paths || {};
      
      if (_.isEmpty(paths)) {
        return { success: true, data: { resourcePath: '', configPath: '' } };
      }
      
      return { success: true, data: paths };
    } catch (error) {
      console.error('读取路径配置错误:', error);
      return { success: false, message: error.message, data: { resourcePath: '', configPath: '' } };
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