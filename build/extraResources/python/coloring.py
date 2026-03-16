import threading
class Coloring:
    def __init__(self):
        self._current_image = None  # 原图
        self._current_processed_image = None  # 当前处理后的图像（用于步骤链）
        self._step_images = {}  # 每个步骤完成后的图像，key为步骤索引

        # 洪水填充控制标志
        self._flood_fill_running = False
        self._flood_fill_stop_event = threading.Event()

        # 步骤处理控制
        self._steps_processing = False
        self._steps_stop_event = threading.Event()

        # 拼接状态
        self._stitched_image = None  # 累积拼接结果（0/1 二值矩阵）
        self._stitch_count = 0


    def 上传图片(self, data):
        pass

    def 保存图片(self, data):
        pass

    def 解析颜色过滤字符串(self, color_str):
        pass