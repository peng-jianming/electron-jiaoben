'use strict';

const { exampleService } = require('../service/example');
const { getSocketServer } = require('ee-core/socket');
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


  获取账号列表(args, event) {
    const accountList = exampleService.获取账号列表();
    return accountList;
  }


  保存账号列表(args, event) {
    try {
      return exampleService.保存账号列表(args);
    } catch (error) {
      console.error('保存账号列表错误:', error);
      return false;
    }
  }

  删除账号(args, event) {
    try {
      return exampleService.删除账号(args);
    } catch (error) {
      console.error('删除账号错误:', error);
      return false;
    }
  }
}
ExampleController.toString = () => '[class ExampleController]';

module.exports = ExampleController; 