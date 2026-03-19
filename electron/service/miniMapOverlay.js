'use strict';

const path = require('path');
const { BrowserWindow, screen, desktopCapturer } = require('electron');
const { getBaseDir } = require('ee-core/ps');
const { getSocketServer } = require('ee-core/socket');

class MiniMapOverlayService {
  constructor() {
    this._win = null;
    this._lastMeta = null;
    this._captureTimer = null;
    this._overlayHiddenForCapture = false;
  }

  async _setOverlayVisibleForCapture(visible) {
    try {
      if (!this._win || this._win.isDestroyed()) return;
      if (visible) {
        if (this._overlayHiddenForCapture) {
          this._overlayHiddenForCapture = false;
          // 恢复可见（不抢焦点）
          if (typeof this._win.setOpacity === 'function') {
            this._win.setOpacity(1);
          }
          if (!this._win.isVisible()) {
            this._win.showInactive();
          }
        }
        return;
      }

      // 隐藏 UI：优先用 opacity=0，避免 hide/show 导致闪烁或焦点变化
      if (!this._overlayHiddenForCapture) {
        this._overlayHiddenForCapture = true;
        if (typeof this._win.setOpacity === 'function') {
          this._win.setOpacity(0);
        } else {
          this._win.hide();
        }
        // 给系统一帧时间完成合成，保证截屏不带 UI
        await new Promise((r) => setTimeout(r, 30));
      }
    } catch (e) {
      // ignore
    }
  }

  _emitMeta() {
    const meta = this.getMeta();
    const socketServer = getSocketServer();
    if (socketServer) {
      socketServer.io.emit('mini-map-meta', meta);
    }
  }

  async _captureOnceMain() {
    try {
      const meta = this.getMeta();
      if (!meta || !meta.bounds || !meta.display) return;

      // 每次截屏都把整个 overlay UI 隐藏，截完再恢复
      await this._setOverlayVisibleForCapture(false);

      const display = meta.display;
      const bounds = meta.bounds;
      const scaleFactor = display.scaleFactor || 1;

      const thumbW = Math.max(1, Math.round((display.size?.width || display.bounds?.width || bounds.width || 1) * scaleFactor));
      const thumbH = Math.max(1, Math.round((display.size?.height || display.bounds?.height || bounds.height || 1) * scaleFactor));

      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: { width: thumbW, height: thumbH },
        fetchWindowIcons: false,
      });
      if (!Array.isArray(sources) || sources.length === 0) return;

      const byId = sources.find((s) => String(s.display_id || '') === String(display.id || ''));
      const source = byId || sources[0];
      if (!source || !source.thumbnail) return;

      const dx = (bounds.x - display.bounds.x) * scaleFactor;
      const dy = (bounds.y - display.bounds.y) * scaleFactor;
      const dw = bounds.width * scaleFactor;
      const dh = bounds.height * scaleFactor;

      const x = Math.max(0, Math.round(dx));
      const y = Math.max(0, Math.round(dy));
      const w = Math.max(1, Math.round(dw));
      const h = Math.max(1, Math.round(dh));

      // 直接使用未缩放的原始截取区域，保证像素尺寸与屏幕实际尺寸一致
      const cropped = source.thumbnail.crop({ x, y, width: w, height: h });
      const dataUrl = cropped.toDataURL();
      if (!dataUrl) return;

      const socketServer = getSocketServer();
      if (socketServer) {
        // 先推原始帧（保证前端有画面）
        socketServer.io.emit('mini-map-frame', {
          image: dataUrl,
          ...meta,
        });

        // 并行交给 Python 做流水线处理（处理后也会回推 mini-map-frame 覆盖）
        socketServer.io.emit('message', {
          类型: '图像处理小地图',
          dataUrl,
        });
      }
    } catch (e) {
      // ignore
    } finally {
      await this._setOverlayVisibleForCapture(true);
    }
  }

  _startCaptureLoop() {
    if (this._captureTimer) return;
    this._captureTimer = setInterval(() => this._captureOnceMain(), 1000);
    this._captureOnceMain();
  }

  _stopCaptureLoop() {
    if (this._captureTimer) {
      clearInterval(this._captureTimer);
    }
    this._captureTimer = null;
  }

  getMeta() {
    if (!this._win || this._win.isDestroyed()) {
      return {
        center: { x: 0, y: 0 },
        radius: 0,
        size: 0,
        bounds: null,
        display: null,
      };
    }

    const bounds = this._win.getBounds(); // DIP
    const size = Math.max(0, Math.round(Math.min(bounds.width || 0, bounds.height || 0)));
    const radius = Math.round(size / 2);
    const centerX = Math.round((bounds.x || 0) + size / 2);
    const centerY = Math.round((bounds.y || 0) + size / 2);
    const disp = screen.getDisplayMatching(bounds);

    return {
      center: { x: centerX, y: centerY },
      radius,
      size,
      bounds: { x: bounds.x, y: bounds.y, width: bounds.width, height: bounds.height },
      display: disp
        ? {
            id: disp.id,
            scaleFactor: disp.scaleFactor,
            bounds: disp.bounds,
            size: disp.size,
          }
        : null,
    };
  }

  async openOverlay(args = {}) {
    if (this._win && !this._win.isDestroyed()) {
      this._win.show();
      this._win.focus();
      this._emitMeta();
      this._startCaptureLoop();
      return { success: true };
    }

    const defaultSize = Math.max(120, Math.min(600, Math.round(args.size || 240)));
    const display = screen.getPrimaryDisplay();
    const workArea = display.workArea; // DIP
    const x = Math.round(workArea.x + (workArea.width - defaultSize) / 2);
    const y = Math.round(workArea.y + (workArea.height - defaultSize) / 2);

    this._win = new BrowserWindow({
      width: defaultSize,
      height: defaultSize,
      x,
      y,
      frame: false,
      transparent: true,
      resizable: false,
      movable: true,
      minimizable: false,
      maximizable: false,
      // skipTaskbar: true,
      alwaysOnTop: true,
      hasShadow: false,
      // focusable: true,
      fullscreenable: false,
      webPreferences: {
        contextIsolation: false,
        nodeIntegration: true,
        // backgroundThrottling: false,
      },
    });

    // 使用静态 overlay 页面作为悬浮框渲染页
    const htmlPath = path.join(getBaseDir(), 'public', 'overlay', 'mini-map-overlay.html');
    await this._win.loadFile(htmlPath);

    this._win.on('closed', () => {
      this._stopCaptureLoop();
      this._win = null;
    });

    const emitIfChanged = () => {
      const meta = this.getMeta();
      const key = JSON.stringify(meta && meta.bounds ? meta.bounds : null) + '|' + meta.size;
      if (this._lastMeta !== key) {
        this._lastMeta = key;
        this._emitMeta();
      }
    };

    this._win.on('move', emitIfChanged);
    this._win.on('resize', emitIfChanged);

    this._emitMeta();
    this._startCaptureLoop();
    return { success: true };
  }

  closeOverlay() {
    if (this._win && !this._win.isDestroyed()) {
      this._win.close();
    }
    this._stopCaptureLoop();
    this._win = null;
    this._emitMeta();
    return { success: true };
  }

  setOverlayBoundsSquare(args = {}) {
    if (!this._win || this._win.isDestroyed()) return { success: false, message: 'overlay not ready' };
    const cur = this._win.getBounds();
    const minSize = 80;
    const maxSize = 1200;

    const size = Math.max(minSize, Math.min(maxSize, Math.round(args.size || Math.min(cur.width, cur.height))));
    const x = Number.isFinite(args.x) ? Math.round(args.x) : cur.x;
    const y = Number.isFinite(args.y) ? Math.round(args.y) : cur.y;

    this._win.setBounds({ x, y, width: size, height: size }, false);
    this._emitMeta();
    return { success: true };
  }
}

module.exports = {
  MiniMapOverlayService,
  miniMapOverlayService: new MiniMapOverlayService(),
};

