'use strict';
const WebSocket = require('ws');
const { logger } = require('ee-core/log');
const path = require('path')
const { getSocketServer } = require('ee-core/socket');
const { getBaseDir } = require('ee-core/ps');
const fs = require('fs');
const tkill = require('tree-kill');
const crossSpawn = require('cross-spawn');

/**
 * 示例服务
 * @class
 */
class ExampleService {

  constructor() {
    // this.deviceProcesses = new Map();
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
    const res = await this.sendRequest(data);
    if (res && res.result) {

      const list = JSON.parse(res.result);

      list.forEach(item => {
        this.deviceProcesses.set(item.deviceId, {
          ...item,
          isRunning: false,
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

  async createPythonServer(name, port) {
    return new Promise((resolve, reject) => {
      const coreProcess = crossSpawn('python', [`./${name}.py`, `--id=${port}`], {
        stdio: ['inherit', 'inherit', 'inherit', 'ipc'],
        detached: false,
        cwd: path.join(getBaseDir(), 'python'),
        maxBuffer: 1024 * 1024 * 1024
      });

      // 开启进程,记录进程id
      const current = this.deviceProcesses.get(port);

      current.pid = coreProcess.pid;
      this.deviceProcesses.set(port, current);

      coreProcess.on('exit', (code, signal) => {
        console.log('Python exit：', name, port, 'code=', code, 'signal=', signal);

        // 结束进程,删除进程id
        const current = this.deviceProcesses.get(port);
        current.pid = null;
        this.deviceProcesses.set(port, current);

        // 无论是否成功退出，都算本次任务结束，交由上层决定是否继续后续任务
        resolve({ code, signal });
      });

      coreProcess.on('error', (err) => {
        // 结束进程,删除进程id
        const current = this.deviceProcesses.get(port);
        current.pid = null;
        this.deviceProcesses.set(port, current);
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

  async 开始任务(deviceList, taskList) {
    const devicePromises = deviceList.map(async (item) => {

      // 任务开始,记录当前任务执行状态
      let res = this.deviceProcesses.get(item.deviceId)
      res.isRunning = true;
      this.deviceProcesses.set(item.deviceId, res)

      this.监听文件(item.deviceId)

      for (const taskName of taskList) {
        try {
          // 运行状态被关了,就不继续执行了
          const current = this.deviceProcesses.get(item.deviceId);
          if (current.isRunning) {
            await this.createPythonServer(taskName, item.deviceId);
          }
        } catch (err) {
          this.deviceProcesses.delete(item.deviceId);
          console.log(`执行任务出错: deviceId=${item.deviceId}, task=${taskName}`, err);
          break; // 执行失败,后续的任务不执行了
        }
      }

      // 任务全部做完, 运行状态结束
      this.deviceProcesses.set(item.deviceId, {
        isRunning: false,
      });
    });
    // 如果希望等所有设备的任务都执行完毕后再返回，可以 await
    await Promise.all(devicePromises);
    this.isRunning = false;
  }

  async 结束任务(deviceList) {
    await Promise.all(deviceList.map((item) => {
      const current = this.deviceProcesses.get(item.deviceId)
      current.isRunning = false;
      this.deviceProcesses.set(item.deviceId, current);
      this.stopPythonServer(item.deviceId)
    }));
  }

  async 监听文件(deviceId) {
    const logPath = path.join(getBaseDir(), `taskLogs/${deviceId}.log`);
    // 若文件不存在则创建，存在则清空内容
    fs.writeFileSync(logPath, '', 'utf8');

    // 移除之前的监听器，防止重复监听
    fs.unwatchFile(logPath);

    // 添加新的监听器
    fs.watchFile(logPath, { interval: 1000 }, (curr, prev) => {
      if (curr.mtime !== prev.mtime) {
        fs.readFile(logPath, 'utf8', (err, data) => {
          if (!err) {
            const arr = data.split('\r\n')
            
            let res = this.deviceProcesses.get(deviceId)
            res.logs = arr[arr.length - 2];
            this.deviceProcesses.set(deviceId, res)
            // SocketServer.io.emit(`${deviceId}`, data);
          }
        });
      }
    });
  }
}
ExampleService.toString = () => '[class ExampleService]';

module.exports = {
  ExampleService,
  exampleService: new ExampleService()
};