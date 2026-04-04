'use strict';
const path = require('path');
const fs = require('fs');
const { getDataDir } = require('ee-core/ps');

class ExampleService {
  constructor() {
    const dataDir = getDataDir();
    this.taskConfigFilePath = path.join(dataDir, '任务配置.json');
  }

  获取任务配置() {
    try {
      if (!fs.existsSync(this.taskConfigFilePath)) {
        return [];
      }
      const raw = fs.readFileSync(this.taskConfigFilePath, 'utf8').trim();
      if (!raw) {
        return [];
      }
      const data = JSON.parse(raw);
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.error('读取任务配置失败:', err);
      return [];
    }
  }

  保存任务配置(args) {
    try {
      const list = args && args.taskSelectValue;
      if (!Array.isArray(list)) {
        return { success: false, message: 'taskSelectValue 须为数组' };
      }
      const dir = path.dirname(this.taskConfigFilePath);
      fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(
        this.taskConfigFilePath,
        JSON.stringify(list, null, 2),
        'utf8'
      );
      return { success: true };
    } catch (err) {
      console.error('保存任务配置失败:', err);
      return { success: false, message: err.message };
    }
  }
}
ExampleService.toString = () => '[class ExampleService]';

module.exports = {
  ExampleService,
  exampleService: new ExampleService()
};