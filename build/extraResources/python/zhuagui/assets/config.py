import os

活动弹框_抓鬼任务 = {
    "标识": "活动弹框_抓鬼任务",
    "方式": "opencv找图",
    "图片路径": os.path.join(os.path.dirname(__file__), "抓鬼任务.png"),
}

钟馗对话 = {
    "标识": "钟馗对话",
    "方式": "opencv找图",
    "图片路径": os.path.join(os.path.dirname(__file__), "钟馗.png"),
}

主界面_抓鬼文字 = {
    "标识": "主界面_抓鬼文字",
    "方式": "opencv找透明图",
    "图片路径": os.path.join(os.path.dirname(__file__), "主界面_抓鬼文字.png"),
}

队伍缺辅助 = {
    "标识": "队伍缺辅助",
    "方式": "opencv找图",
    '关闭区域': {"x": 935, "y": 642, "w": 205, "h": 65},
    "图片路径": os.path.join(os.path.dirname(__file__), "队伍缺辅助.png"),
}