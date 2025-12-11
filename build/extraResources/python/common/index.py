import sys
import os

# 将父目录添加到 Python 路径，以便能找到 common 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index import InterfaceStateMachine, Field, 截图
from common.assets import config as common_assets


class StateMachine(InterfaceStateMachine):
    def __init__(self):
        super().__init__()

        def 识别屏幕():
            url = 截图()
            if Field(common_assets.活动界面).设置大图路径(url).查找().是否找到():
               return "活动界面" if "活动界面" in self._states else  Field(common_assets.弹框_关闭).查找().点击().随机延时(1, 2)
            if Field(common_assets.队伍弹框界面).设置大图路径(url).查找().是否找到():
               return "队伍弹框界面" if "队伍弹框界面" in self._states else  Field(common_assets.弹框_关闭).查找().点击().随机延时(1, 2)
            if Field(common_assets.福利弹框界面).设置大图路径(url).查找().是否找到():
               return "福利弹框界面" if "福利弹框界面" in self._states else  Field(common_assets.福利弹框界面_关闭).查找().点击().随机延时(1, 2)
            if Field(common_assets.便捷组队弹框界面).设置大图路径(url).查找().是否找到():
               return "便捷组队弹框界面" if "便捷组队弹框界面" in self._states else  Field(common_assets.弹框_关闭).查找().点击().随机延时(1, 2)
            if Field(common_assets.调整组队等级界面).设置大图路径(url).查找().是否找到():
               return "调整组队等级界面" if "调整组队等级界面" in self._states else  Field(common_assets.调整组队等级界面_关闭).查找().点击().随机延时(1, 2)
            if Field(common_assets.加入帮派界面).设置大图路径(url).查找().是否找到():
               return "加入帮派界面" if "加入帮派界面" in self._states else  Field(common_assets.加入帮派界面_关闭).查找().点击().随机延时(1, 2)
            if Field(common_assets.战斗界面).设置大图路径(url).查找().是否找到():
               return "战斗界面"

            if (
                Field(common_assets.主界面活动按钮)
                .设置查找区域({"x": 553, "y": 0, "w": 122, "h": 126})
                .设置大图路径(url)
                .查找()
                .是否找到()
            ):
                return "主界面"

        self.set_recognizer(识别屏幕)


if __name__ == "__main__":
    sm = StateMachine()
    result = sm.start()
