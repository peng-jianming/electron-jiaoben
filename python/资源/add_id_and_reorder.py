# -*- coding: utf-8 -*-
"""给字库.json 每项：名字放到第一属性，并增加 id（uuid）"""
import json
import uuid
from pathlib import Path

def main():
    json_path = Path(__file__).parent / "字库.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for item in data:
        out.append({
            "名字": item["名字"],
            "id": uuid.uuid4().hex[:8],
            "点阵": item["点阵"],
            "长宽有效数量": item["长宽有效数量"],
            "偏色": item["偏色"],
            "偏移点击区域": item["偏移点击区域"],
        })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"已更新 {len(out)} 条：名字置首并添加 id")

if __name__ == "__main__":
    main()
