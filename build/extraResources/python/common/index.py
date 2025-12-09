import sys
import os

# 将父目录添加到 Python 路径，以便能找到 common 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index import InterfaceStateMachine, Field
from common.assets import config as common_assets



class StateMachine(InterfaceStateMachine):
    def __init__(self):
        super().__init__()
        self.set_recognizer(self.识别屏幕)

        self.on("活动弹框界面", self.关闭活动弹框界面)
        self.on("队伍弹框界面", self.关闭队伍弹框界面)
        self.on("福利弹框界面", self.关闭福利弹框界面)
        self.on("便捷组队弹框界面", self.关闭便捷组队弹框界面)


    def 识别屏幕(self):
        if Field(common_assets.通用_活动界面).查找().是否找到():
            return "活动弹框界面"
        if Field(common_assets.通用_队伍弹框界面).查找().是否找到():
            return "队伍弹框界面"
        if Field(common_assets.通用_福利弹框界面).查找().是否找到():
            return "福利弹框界面"
        if Field(common_assets.通用_便捷组队弹框界面).查找().是否找到():
            return "便捷组队弹框界面"
        if Field(common_assets.通用_调整组队等级界面).查找().是否找到():
            return "调整组队等级界面"


        if (
            Field(common_assets.通用_主界面活动按钮)
            .设置查找区域({"x": 553, "y": 0, "w": 122, "h": 126})
            .查找()
            .是否找到()
        ):
            return "主界面"


    def 关闭活动弹框界面(self, context):
        Field(common_assets.弹框_关闭).查找().点击()
        
    def 关闭队伍弹框界面(self, context):
        Field(common_assets.弹框_关闭).查找().点击()

    def 关闭福利弹框界面(self, context):
        Field(common_assets.通用_福利弹框界面_关闭).查找().点击()
        
    def 关闭便捷组队弹框界面(self, context):
        Field(common_assets.弹框_关闭).查找().点击()





if __name__ == "__main__":
    sm = StateMachine()
    result = sm.start()