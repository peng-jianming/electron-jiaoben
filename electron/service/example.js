'use strict';
const path = require('path');
const fs = require('fs');
const { getDataDir } = require('ee-core/ps');

class ExampleService {
  constructor() {
    const dataDir = getDataDir();
    this.accountFilePath = path.join(dataDir, '账号信息.json');
    // 任务配置文件路径：用于持久化「已选任务列表」和「任务配置」
    this.taskConfigFilePath = path.join(dataDir, '任务配置.json');
  }

  获取账号列表() {
    if (!fs.existsSync(this.accountFilePath)) {
      return [];
    }
    try {
      const content = fs.readFileSync(this.accountFilePath, 'utf8');

      const list = JSON.parse(content);
      return Array.isArray(list) ? list : [];
    } catch (e) {
      return [];
    }
  }

  保存账号列表(args) {
    if (args && !Array.isArray(args.accountList)) {
      return false;
    }
    fs.writeFileSync(this.accountFilePath, JSON.stringify(args.accountList, null, 2), 'utf8');
    return true;
  }

  /**
   * 获取任务配置
   * 返回格式：{ selectedTasks: string[], taskConfig: any }
   */
  获取任务配置() {
    // 默认结构：空任务列表与空配置
    const defaultValue = {
      selectedTasks: [],
      taskConfig: []
    };

    if (!fs.existsSync(this.taskConfigFilePath)) {
      return defaultValue;
    }

    try {
      const content = fs.readFileSync(this.taskConfigFilePath, 'utf8');
      const data = JSON.parse(content);

      if (!data || typeof data !== 'object') {
        return defaultValue;
      }

      const selectedTasks = Array.isArray(data.selectedTasks) ? data.selectedTasks : [];
      // taskConfig 可能是数组（按顺序）或对象（兼容旧格式），这里直接透传，由前端自行兼容
      const taskConfig = data.taskConfig != null ? data.taskConfig : [];

      return {
        selectedTasks,
        taskConfig
      };
    } catch (e) {
      return defaultValue;
    }
  }

  /**
   * 保存任务配置
   * @param {Object} args
   *   - args.taskSelectValue: { selectedTasks, taskConfig }
   *   - 或直接为 { selectedTasks, taskConfig }
   */
  保存任务配置(args) {
    if (!args) {
      return false;
    }

    const payload = args.taskSelectValue && typeof args.taskSelectValue === 'object'
      ? args.taskSelectValue
      : args;

    if (!payload || typeof payload !== 'object') {
      return false;
    }

    const selectedTasks = Array.isArray(payload.selectedTasks) ? payload.selectedTasks : [];
    const taskConfig = payload.taskConfig != null ? payload.taskConfig : [];

    const data = {
      selectedTasks,
      taskConfig
    };

    fs.writeFileSync(this.taskConfigFilePath, JSON.stringify(data, null, 2), 'utf8');
    return true;
  }
}
ExampleService.toString = () => '[class ExampleService]';

module.exports = {
  ExampleService,
  exampleService: new ExampleService()
};