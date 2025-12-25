/*************************************************
 ** preload为预加载模块，该文件将会在程序启动时加载 **
 *************************************************/

const { logger } = require('ee-core/log');
const { cross } = require('ee-core/cross');
const path = require("path");
const { getExtraResourcesDir } = require('ee-core/ps');

const createPythonServer = async () => {
  const serviceName = "python";
  const opt = {
    name: 'pyapp',
    cmd: path.join(getExtraResourcesDir(), 'py', 'pyapp'),
    directory: path.join(getExtraResourcesDir(), 'py'),
    args: ['--port=7074'],
    windowsExtname: true,
    appExit: true,
  }
  const entity = await cross.run(serviceName, opt);
  logger.info('server name:', entity.name);
  logger.info('server config:', entity.config);
  logger.info('server url:', entity.getUrl());
}


const abc = () => {
  const coreProcess = crossSpawn('C:/ProgramData/anaconda3/python.exe', [ `./python/index.py`], {
    stdio: ['inherit', 'inherit', 'inherit', 'ipc'],
    detached: false,
    cwd: path.join(getExtraResourcesDir(), 'py'),
    maxBuffer: 1024 * 1024 * 1024,
    windowsHide: true
  });
  

    coreProcess.on('exit', (code, signal) => {
      logger.info('Python exit：', 'code=', code, 'signal=', signal);
    });

    coreProcess.on('error', (err) => {
      logger.error('Python error：', err);
    });
}


function preload() {
  // createPythonServer()




  logger.info('[preload] load 1');

}

/**
* 预加载模块入口
*/
module.exports = {
  preload
}