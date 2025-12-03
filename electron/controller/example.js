'use strict';

const { exampleService } = require('../service/example');

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
   const list =  await exampleService.获取设备列表();   
   return list;
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