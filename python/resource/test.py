import os
import sys
from typing import Dict, List, Optional


def load_config() -> Dict[str, List[int]]:
    """
    从 config.py 中的 界面集合33 生成:
    { 查找字符串: 偏移点击区域 or [0,0,0,0] }
    """
    # 将上级目录 (python) 加入 sys.path，方便导入 resource.config
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    from resource.config import 界面集合33  # type: ignore

    mapping: Dict[str, List[int]] = {}

    def add_item(find_str: Optional[str], offset: Optional[List[int]]) -> None:
        if not find_str:
            return
        if offset is None:
            mapping[find_str] = [0, 0, 0, 0]
        else:
            # 确保是长度为 4 的列表
            if len(offset) == 4:
                mapping[find_str] = list(offset)
            else:
                mapping[find_str] = [0, 0, 0, 0]

    for _, ui_conf in 界面集合33.items():  # type: ignore[name-defined]
        if not isinstance(ui_conf, dict):
            continue

        # 顶层界面本身的查找字符串 (无偏移，统一用 0,0,0,0)
        top_find = ui_conf.get("查找字符串")
        add_item(top_find, None)

        # 状态
        state_conf = ui_conf.get("状态") or {}
        if isinstance(state_conf, dict):
            for _state_name, state in state_conf.items():
                if isinstance(state, dict):
                    find_str = state.get("查找字符串")
                    offset = state.get("偏移点击区域")
                    add_item(find_str, offset)

        # 按钮
        btn_conf = ui_conf.get("按钮") or {}
        if isinstance(btn_conf, dict):
            for _btn_name, btn in btn_conf.items():
                # 只有 dict 并且含有查找字符串的按钮需要进字库
                if isinstance(btn, dict):
                    find_str = btn.get("查找字符串")
                    offset = btn.get("偏移点击区域")
                    add_item(find_str, offset)

    return mapping


def update_font_library(font_path: str, mapping: Dict[str, List[int]]) -> None:
    """
    根据 mapping 更新字库:
    - 匹配到查找字符串时，在行末追加 &x,y,w,h
    - 如果已经有偏移段 (&x,y,w,h)，则覆盖为新的值

    约定:
    原始行结构: data & pos & colors & label
    更新后:    data & pos & colors & label & offset
    label 始终使用第 4 段 (index=3)
    """
    if not os.path.exists(font_path):
        raise FileNotFoundError(font_path)

    with open(font_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines: List[str] = []

    for line in lines:
        raw = line.rstrip("\n")
        if not raw.strip():
            new_lines.append(line)
            continue

        parts = raw.split("&")
        # 正常应该至少有 4 段
        if len(parts) < 4:
            new_lines.append(line)
            continue

        label = parts[3]
        if label in mapping:
            offset = mapping[label]
            offset_str = ",".join(str(v) for v in offset)
            if len(parts) >= 5:
                # 已经有偏移段，直接覆盖
                parts[4] = offset_str
            else:
                # 追加新的偏移段
                parts.append(offset_str)

            raw = "&".join(parts)
            new_lines.append(raw + "\n")
        else:
            new_lines.append(line)

    # 写回文件
    with open(font_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def main() -> None:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "font_library.txt")

    mapping = load_config()
    update_font_library(font_path, mapping)
    print("font_library.txt 已根据 界面集合33 更新偏移点击区域。")


if __name__ == "__main__":
    main()



