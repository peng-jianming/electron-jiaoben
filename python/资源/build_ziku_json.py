# -*- coding: utf-8 -*-
"""将字库.txt 按 点阵&长宽有效数量&偏色&名字&偏移点击区域 解析为 字库.json"""
import json
from pathlib import Path

def main():
    txt_path = Path(__file__).parent / "字库.txt"
    json_path = Path(__file__).parent / "字库.json"
    rows = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("&")
            if len(parts) != 5:
                continue
            点阵, 长宽有效数量, 偏色, 名字, 偏移点击区域 = parts
            rows.append({
                "点阵": 点阵,
                "长宽有效数量": 长宽有效数量,
                "偏色": 偏色,
                "名字": 名字,
                "偏移点击区域": 偏移点击区域,
            })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"已写入 {len(rows)} 条到 {json_path}")

if __name__ == "__main__":
    main()
