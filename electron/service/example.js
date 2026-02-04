'use strict';
const path = require('path');
const fs = require('fs');
const { getDataDir } = require('ee-core/ps');

class ExampleService {
  constructor() {
    const dataDir = getDataDir();
    this.accountFilePath = path.join(dataDir, '账号信息.json');
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
}
ExampleService.toString = () => '[class ExampleService]';

module.exports = {
  ExampleService,
  exampleService: new ExampleService()
};