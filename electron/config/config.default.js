'use strict';

const path = require('path');
const { getBaseDir } = require('ee-core/ps');

/**
 * 默认配置
 */
module.exports = () => {
  return {
    openDevTools: true,
    singleLock: false,
    windowsOption: {
      title: 'mhxy',
      width: 1920,
      height: 1080,
      minWidth: 1920,
      minHeight: 1080,
      maxWidth: 1920,
      maxHeight: 1080,
      webPreferences: {
        //webSecurity: false,
        contextIsolation: false, // false -> 可在渲染进程中使用electron的api，true->需要bridge.js(contextBridge)
        nodeIntegration: true,
        //preload: path.join(getElectronDir(), 'preload', 'bridge.js'),
      },
      frame: false,
      show: true,
      icon: path.join(getBaseDir(), 'public', 'images', 'logo-32.png'),
    },
    logger: {
      level: 'INFO',
      outputJSON: false,
      appLogName: 'ee.log',
      coreLogName: 'ee-core.log',
      errorLogName: 'ee-error.log' 
    },
    remote: {
      enable: false,
      url: 'http://electron-egg.kaka996.com/'
    },
    socketServer: {
      enable: true,
      port: 7072,
      path: "/socket.io/",
      connectTimeout: 45000,
      pingTimeout: 30000,
      pingInterval: 25000,
      maxHttpBufferSize: 1e8,
      transports: ["polling", "websocket"],
      cors: {
        origin: true,
      },
      channel: 'socket-channel'
    },
    httpServer: {
      enable: false,
      https: {
        enable: false, 
        key: '/public/ssl/localhost+1.key',
        cert: '/public/ssl/localhost+1.pem'
      },
      host: '127.0.0.1',
      port: 7071,
    },
    mainServer: {
      indexPath: '/public/dist/index.html',
      channelSeparator: '/',
    }
  }
}
