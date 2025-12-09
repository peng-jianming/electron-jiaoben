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


    def 识别屏幕(self):
        if Field(common_assets.通用_活动界面).查找().是否找到():
            return "活动弹框界面"
        if Field(common_assets.通用_队伍弹框界面).查找().是否找到():
            return "队伍弹框界面"


        # 需要判断的已经判断完了,最后肯定是主界面,即使不是主界面,那么就直接退回主界面
        # 返回主界面() // 进行返回主界面
        if (
            Field(common_assets.通用_主界面活动按钮)
            .设置查找区域({"x": 553, "y": 0, "w": 122, "h": 126})
            .查找()
            .是否找到()
        ):
            return "主界面"


    def 关闭活动弹框界面(self):
        Field(common_assets.弹框_关闭).查找().点击()
        
    def 关闭队伍弹框界面(self):
        1
