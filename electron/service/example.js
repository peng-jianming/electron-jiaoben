'use strict';
const WebSocket = require('ws');
const { logger } = require('ee-core/log');
const path = require('path')
const { getSocketServer } = require('ee-core/socket');
const { getBaseDir, getExtraResourcesDir } = require('ee-core/ps');
const fs = require('fs');
const tkill = require('tree-kill');
const crossSpawn = require('cross-spawn');

class ExampleService {

  constructor() {
    const deviceMap = new Map();
    this.deviceProcesses = new Proxy(deviceMap, {
      get(target, prop, receiver) {
        
        if (prop === 'set') {
          return (key, value) => {
            const result = target.set(key, value);
            try {
              const SocketServer = getSocketServer();
              if (SocketServer && SocketServer.io) {
                SocketServer.io.emit(`${key}`, value);
              }
            } catch (err) {
              logger.error('Socket emit error:', err);
            }
            return result;
          };
        }
        const value = Reflect.get(target, prop, receiver);
        if (typeof value === 'function') {
          return value.bind(target);
        }
        return value;
      }
    });
  }

  async 获取设备列表() {
    const data = {
      "action": "list"
    };
    // const res = await this.sendRequest(data);
    const res = {
      result: "[{\"deviceId\":\"1\",\"name\":\"设备1\",\"logs\":\"\"},{\"deviceId\":\"2\",\"name\":\"设备2\",\"logs\":\"\"},{\"deviceId\":\"3\",\"name\":\"设备3\",\"logs\":\"\"}]"
    }
    
    if (res && res.result) {
      const list = JSON.parse(res.result);
      list.forEach(item => {
        this.deviceProcesses.set(item.deviceId, {
          ...item,
          logs: ''
        });
      })
      return [...this.deviceProcesses.values()];
    }
    return [];
  }

  sendRequest(payload) {

    return new Promise((resolve, reject) => {
      const ws = new WebSocket('ws://127.0.0.1:33332');

      ws.on('open', () => {
        try {
          ws.send(JSON.stringify(payload));
        } catch (e) {
          ws.close();
          reject(e);
        }
      });

      ws.on('message', (data) => {
        try {
          const res = JSON.parse(data);
          resolve(res);
        } catch (error) {
          console.log('极限投屏返回错误', error.message);
          resolve(null);
        } finally {
          ws.close();
        }
      });

      ws.on('error', (err) => {
        console.log('连接投屏出错了');
        reject(err);
        ws.close();
      });
    });
  }

  changeDeviceProcesses(id, key, value) {
    const current = this.deviceProcesses.get(id);

    if(current) {
      current[key] = value;
      this.deviceProcesses.set(id, current);
    }
  }

  async createPythonServer(runPath, port) {
    return new Promise((resolve, reject) => {
    const coreProcess = crossSpawn('C:/ProgramData/anaconda3/python.exe', [ `${runPath}/index.py`, `--ids=${port}`], {
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

module.exports = {
  ExampleService,
  exampleService: new ExampleService()
};