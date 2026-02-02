'use strict';
const path = require('path');
const fs = require('fs');
const { getDataDir } = require('ee-core/ps');

class ExampleService {
  constructor() {
    const dataDir = getDataDir();
    this.accountFilePath = path.join(dataDir, 'account.json');
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
    const accountList = args && (Array.isArray(args) ? args : args.accountList);
    if (!Array.isArray(accountList)) {
      return false;
    }
    fs.writeFileSync(this.accountFilePath, JSON.stringify(accountList, null, 2), 'utf8');
    return true;
  }

  删除账号(args) {
    const list = this.获取账号列表();
    const index = args && (typeof args.index === 'number' ? args.index : args.id);
    if (typeof index !== 'number' || index < 0 || index >= list.length) {
      return false;
    }
    list.splice(index, 1);
    return this.保存账号列表(list);
  }
}
ExampleService.toString = () => '[class ExampleService]';

module.exports = {
  ExampleService,
  exampleService: new ExampleService()
};