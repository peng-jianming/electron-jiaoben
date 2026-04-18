from 通信管理器 import 通信管理器类
from ImageProcessorTab import (
    加载图片库,
    图片库模板匹配,
    重命名图片库项,
    保存图片到图片库,
    保存图片库,
    字库匹配,
    获取设备列表,
    设置当前设备,
    截图当前设备,
)


class 主程序:
    def __init__(self):
        # 通信管理器：负责 socket.io 连接、消息转发与队列处理
        self.通信管理器 = 通信管理器类(
            服务器地址="http://127.0.0.1:7070",
            消息处理回调=self.客户端消息队列处理,
        )

    def 客户端消息队列处理(self, 类型, 数据):
        """供通信管理器在消息队列线程中回调，处理单条消息。"""
        处理器 = {
            "get_devices": 获取设备列表,
            "set_device": 设置当前设备,
            "capture_screenshot": 截图当前设备,
            "load_image_library": 加载图片库,
            "image_library_match": 图片库模板匹配,
            "save_image_to_library": 保存图片到图片库,
            "save_image_library": 保存图片库,
            "rename_image_library_item": 重命名图片库项,
            "font_library_match": 字库匹配,
        }

        处理函数 = 处理器.get(类型)
        if not 处理函数:
            print(f"未知消息类型: {类型}")
            return

        try:
            result = 处理函数(数据)
        except Exception as e:
            print(f"处理消息 {类型} 时异常: {e}")
            return
        if isinstance(result, dict) and "prop" in result and "message" in result:
            self.通信管理器.发送到Electron(result)
        else:
            # 某些处理函数可能选择不向前端返回内容
            pass


if __name__ == "__main__":
    app = 主程序()
    app.通信管理器.阻塞直到断开()