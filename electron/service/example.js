'use strict';
const WebSocket = require('ws');
const { logger } = require('ee-core/log');
const path = require('path')
const { getExtraResourcesDir, getLogDir } = require('ee-core/ps');


const tkill = require('tree-kill');

const crossSpawn = require('cross-spawn');

// 封装为 Promise，方便上层统一 await
const kill = (id) => {
  return new Promise((resolve) => {
    tkill(id, 'SIGINT', (err) => {
      if (err) {
        // 如果 SIGINT 失败，再尝试 SIGKILL，最终无论如何都认为结束
        tkill(id, 'SIGKILL', () => resolve());
      } else {
        resolve();
      }
    });
  });
};

/**
 * 示例服务
 * @class
 */
class ExampleService {

  constructor() {
    // 记录每个设备对应的 Python 任务进程 PID 列表：{ [deviceId]: number[] }
    this.deviceProcesses = new Map();
  }

  async 获取设备列表() {
    const data = {
      "action": "list"
    };
    const res = await this.sendRequest(data);
    if (res && res.result) {
      return JSON.parse(res.result);
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
      const coreProcess = crossSpawn('C:/Users/管理员/AppData/Local/Programs/Python/Python312-32/python.exe', [`./${name}.py`, `--id=${port}`], {
        stdio: ['inherit', 'inherit', 'inherit', 'ipc'],
        detached: false,
        cwd: 'D:/pjm/vvvvvvvvvvvvv/electron-egg/python',
        maxBuffer: 1024 * 1024 * 1024
      });

      // 开启进程,记录进程id
      const current = this.deviceProcesses.get(port);
      console.log('current', current);
      
      current.pid = coreProcess.pid;
      this.deviceProcesses.set(port, current);

      coreProcess.on('exit', (code, signal) => {
        console.log('Python 任务退出：', name, port, 'code=', code, 'signal=', signal);

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

  async stopPythonServer(deviceId) {
    const current = this.deviceProcesses.get(deviceId)
    if (!current || !current.pid) return;

    console.log(current.pid, "--------------");
    
    await kill(current.pid);
  }

  async 开始任务(deviceList, taskList) {


    const devicePromises = deviceList.map(async (item) => {

      // 任务开始,记录当前任务执行状态
      this.deviceProcesses.set(item.deviceId, {
        isRunning: true,
      });

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
    console.log('1111111111');
    
    await Promise.all(deviceList.map((item) => {
      const current = this.deviceProcesses.get(item.deviceId)
      current.isRunning = false;
      this.deviceProcesses.set(item.deviceId, current);
      this.stopPythonServer(item.deviceId)
    }));
  }
}
ExampleService.toString = () => '[class ExampleService]';

module.exports = {
  ExampleService,
  exampleService: new ExampleService()
};