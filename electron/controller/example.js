'use strict';

const { exampleService } = require('../service/example');
const { getSocketServer } = require('ee-core/socket');
const { getBaseDir, getExtraResourcesDir } = require('ee-core/ps');
const path = require('path');
const crossSpawn = require('cross-spawn');
const {
  getMainWindow
} = require('ee-core/electron/window');
const { miniMapOverlayService } = require('../service/miniMapOverlay');
class ExampleController {

  /**
   * 所有方法接收两个参数
   * @param args 前端传的参数
   * @param event - ipc通信时才有值。详情见：控制器文档
   */

  async 启动后端服务(args, event) {
    const coreProcess = crossSpawn('C:/ProgramData/anaconda3/python.exe', [path.join(getBaseDir(), 'python', 'index.py')], {
      stdio: ['inherit', 'inherit', 'inherit', 'ipc'],
      detached: false,
      maxBuffer: 1024 * 1024 * 1024,
      windowsHide: true
    });
    coreProcess.on('exit', (code, signal) => {
      logger.info('Python exit：', 'code=', code, 'signal=', signal);
    });

    coreProcess.on('error', (err) => {
      logger.error('Python error：', err);
    });
  }

  /**
  * 接收 后端 的数据,根据传的事件名直接转发前端,在这不做任何处理
  * @param {Object} args - 参数对象
  * @param {Object} event - 事件对象
  */
  从后端接收数据(args, event) {

    try {
      // 通过 type 来决定发送给前端哪个事件
      const 事件名 = args.事件名;
      const 数据 = args.数据;

      const socketServer = getSocketServer();
      if (socketServer) {
        socketServer.io.emit(事件名, 数据);
      }

    } catch (error) {
      console.error('发送处理结果错误:', error);
      return { success: false, message: error.message };
    }
  }


  /**
 * 发送消息到 后端 客户端, 直接转发,在这不做任何处理
 * @param {Object} args - 参数对象
 * @param {Object} event - 事件对象
 */
  发送到后端(args, event) {
    try {
      // 获取 socket 服务器实例
      const socketServer = getSocketServer();

      if (!socketServer) {
        console.error('Socket 服务器未初始化');
        return { success: false, message: 'Socket 服务器未初始化' };
      }

      // 向所有连接的客户端发送消息
      // 事件名：'message'
      // 数据：args 对象
      socketServer.io.emit('message', args);

      return { success: true, message: '消息已发送' };
    } catch (error) {
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

  // ===== 小地图实时截屏悬浮框 =====
  async 打开小地图截屏框(args, event) {
    return await miniMapOverlayService.openOverlay(args || {});
  }

  关闭小地图截屏框(args, event) {
    return miniMapOverlayService.closeOverlay();
  }

  设置小地图截屏框正方形范围(args, event) {
    return miniMapOverlayService.setOverlayBoundsSquare(args || {});
  }

  获取小地图截屏框信息(args, event) {
    return miniMapOverlayService.getMeta();
  }

}
ExampleController.toString = () => '[class ExampleController]';

module.exports = ExampleController; 