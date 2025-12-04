import os
from ultralytics import YOLO

# 获取模型路径（与当前文件同目录下的best.pt）
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best.pt')

# 加载模型（全局加载，避免重复加载）
_model = None


def get_model():
    """获取YOLO模型实例（懒加载）"""
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model


def detect_objects(image_path, conf_threshold=0.25):
    """
    使用YOLOv8模型检测图片中的目标
    
    参数:
        image_path: 图片路径
        conf_threshold: 置信度阈值，默认0.25
    
    返回:
        检测结果列表，每个元素是一个字典，包含:
        - class_name: 分类名
        - confidence: 相似度/置信度
        - x: 边界框中心x坐标
        - y: 边界框中心y坐标
        - w: 边界框宽度
        - h: 边界框高度
    """
    model = get_model()
    
    # 进行推理
    results = model(image_path, conf=conf_threshold, verbose=False)
    
    detections = []
    
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
            
        for i in range(len(boxes)):
            # 获取边界框坐标 (xywh格式: 中心点x, 中心点y, 宽度, 高度)
            xywh = boxes.xywh[i].tolist()
            x, y, w, h = xywh
            
            # 获取置信度
            confidence = float(boxes.conf[i])
            
            # 获取类别ID和类别名
            class_id = int(boxes.cls[i])
            class_name = model.names[class_id]
            
            detection = {
                'class_name': class_name,
                'confidence': confidence,
                'x': x,
                'y': y,
                'w': w,
                'h': h
            }
            detections.append(detection)
    
    return detections


if __name__ == '__main__':
    # 测试示例
    import sys
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        results = detect_objects(test_image)
        print(f"检测到 {len(results)} 个目标:")
        for r in results:
            print(f"  - {r['class_name']}: 置信度={r['confidence']:.2f}, "
                  f"位置=({r['x']:.1f}, {r['y']:.1f}), "
                  f"尺寸=({r['w']:.1f} x {r['h']:.1f})")
    else:
        print("用法: python bbb.py <图片路径>")

