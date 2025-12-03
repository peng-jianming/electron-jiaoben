'use strict';

const { logger, createLog } = require('ee-core/log');
const { exampleService } = require('../service/example');
const { getSocketServer } = require('ee-core/socket');
const fs = require('fs');
const path = require('path');

const { getBaseDir } = require('ee-core/ps');
/**
 * example
 * @class
 */
class ExampleController {

  /**
   * 所有方法接收两个参数
   * @param args 前端传的参数
   * @param event - ipc通信时才有值。详情见：控制器文档
   */

  async 获取设备列表() {
    const data = {
      "action": "list"
    };
    const res = await exampleService.sendRequest(data);
    if (res && res.result) {

      const list = JSON.parse(res.result);

      const SocketServer = getSocketServer();
      list.forEach(item => {

        const logPath = path.join(getBaseDir(), `taskLogs/${item.deviceId}.log`);
        // 若文件不存在则创建，存在则清空内容
        fs.writeFileSync(logPath, '', 'utf8');

        // 移除之前的监听器，防止重复监听
        fs.unwatchFile(logPath);

        // 添加新的监听器
        fs.watchFile(logPath, { interval: 1000 }, (curr, prev) => {
          if (curr.mtime !== prev.mtime) {
            fs.readFile(logPath, 'utf8', (err, data) => {
              if (!err) {
                SocketServer.io.emit(`${item.deviceId}`, data);
              }
            });
          }
        });

      })
      return list;
    }
    return [];
  }

  async 开始任务(args, event) {
    const params = args || {};
    await exampleService.开始任务(JSON.parse(params.deviceList || '[]'), params.taskList);
  }


  async 结束任务(args, event) {
    const params = args || {};
    await exampleService.结束任务(JSON.parse(params.deviceList || '[]'));
  }

}
ExampleController.toString = () => '[class ExampleController]';

module.exports = ExampleController; 