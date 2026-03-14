# -*- coding: utf-8 -*-
"""
将 界面配置.json 按模板补全：
- 界面层级：补全 类型、查找区域、相似度、按钮、状态、滑动区域、识字区域（已有不动）
- 按钮/状态 下值为对象：补全 类型=点阵、查找区域、相似度（已有不动）
- 按钮/状态 下值为字符串：改为 { "类型": "固定区域", "固定区域": 原字符串 }
"""

import json
import os

# 界面层级的默认模板（仅用于补缺失的 key）
INTERFACE_TEMPLATE = {
    "类型": "点阵",
    "查找区域": "",
    "相似度": 0.9,
    "按钮": {},
    "状态": {},
    "滑动区域": {},
    "识字区域": {},
}

# 按钮/状态下“对象”类型的默认模板（仅用于补缺失的 key）
BUTTON_OR_STATE_OBJECT_TEMPLATE = {
    "类型": "点阵",
    "查找区域": "",
    "相似度": 0.9,
}


def ensure_interface_shape(interface: dict) -> dict:
    """界面层级：缺失的 key 按模板补上，已有不动。"""
    for key, default in INTERFACE_TEMPLATE.items():
        if key not in interface:
            interface[key] = default.copy() if isinstance(default, dict) else default
    return interface


def normalize_button_or_state_value(key: str, value) -> dict:
    """
    按钮/状态下的某一项：
    - 值为字符串 -> { "类型": "固定区域", "固定区域": 原字符串 }
    - 值为对象 -> 补全 类型、查找区域、相似度，其余保留
    """
    if isinstance(value, str):
        return {"类型": "固定区域", "固定点击区域": value}
    if isinstance(value, dict):
        out = value.copy()
        for k, v in BUTTON_OR_STATE_OBJECT_TEMPLATE.items():
            if k not in out:
                out[k] = v
        return out
    return value


def process_buttons_and_states(interface: dict) -> None:
    """对 按钮、状态 下的每个属性按规则处理（就地修改）。"""
    for section in ("按钮", "状态"):
        if section not in interface or not isinstance(interface[section], dict):
            continue
        for k, v in list(interface[section].items()):
            interface[section][k] = normalize_button_or_state_value(k, v)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "界面配置.json")
    out_path = os.path.join(base_dir, "界面配置.json")  # 同文件覆盖

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for name, interface in data.items():
        if not isinstance(interface, dict):
            continue
        ensure_interface_shape(interface)
        process_buttons_and_states(interface)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("已处理并写回: 界面配置.json")


if __name__ == "__main__":
    main()
