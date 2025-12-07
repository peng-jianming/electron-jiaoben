import sys
import os

# 将父目录添加到 Python 路径，以便能找到 common 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.index import StateMachine, Field
from common.assets import config as common_assets
from zhuagui.assets import config as zhuagui_assets

sm = StateMachine()

@sm.state("回到主界面")
def _():
    return "打开活动界面"

@sm.state("打开活动界面")
def _():
    Field(common_assets.通用_主界面活动按钮).查找().点击().随机延时(1, 2)
    return (
        "参加抓鬼"
        if Field(common_assets.通用_活动界面).查找().是否找到()
        else "回到主界面"
    )

@sm.state("参加抓鬼,匹配组队")
def _():
    field = Field(zhuagui_assets.活动弹框_抓鬼任务).查找()
    if field.是否找到():
        Field(common_assets.通用_活动界面未完成参加按钮).设置查找区域({'x': field.x, 'y': field.y, 'w': 448, 'h': 137}).查找().点击().随机延时(1,2)
        Field(zhuagui_assets.便捷组队弹框_自动匹配).查找().点击().随机延时(1,2)
        if Field(zhuagui_assets.便捷组队弹框_取消匹配).查找().是否找到():
            return '抓鬼任务中'
        
    return '回到主界面'



if __name__ == "__main__":
    print( "开始")
    result = sm.start("回到主界面")
    print(f"状态机执行完成，返回结果: '{result}'")