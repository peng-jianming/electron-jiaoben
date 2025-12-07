import os

# 获取模型文件的绝对路径
_model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'tools', 'best.pt')

对话选项框 = {
    '标识': '对话选项框',
    '方式': 'yolo',
    '分类名': '对话框',
    '相似度': 0.7,
    '模型路径': _model_path
}

对话说话框 = {
    '标识': '对话说话框',
    '方式': 'yolo',
    '分类名': '说话框',
    '相似度': 0.7,
    '模型路径': _model_path
}


__all__ = ['对话选项框', '对话说话框']
