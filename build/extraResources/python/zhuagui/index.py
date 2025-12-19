import sys
import os

# 将父目录添加到 Python 路径，以便能找到 common 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index import Field, 随机ADB点击, ADB点击, 随机延时, TaskLineMachine
from common.assets import config as common_assets
from zhuagui.assets import config as zhuagui_assets

sm = TaskLineMachine()

sm.update_context(action="接取任务")
sm.update_context(是否已选择完队伍等级=False)

@sm.state(common_assets.主界面活动按钮)
def _(context):
    if context["action"] == "接取任务":
        # 钟馗对话,点击抓鬼任务
        if Field(zhuagui_assets.钟馗对话).查找().点击(1829, 361, 403, 66).随机延时(2, 3).是否找到():
            context["action"] = "任务中"
        else:   
            Field(common_assets.主界面活动按钮).查找().点击().随机延时(1, 2)

    if context["action"] == "任务中":
        Field(common_assets.主界面_未选中任务).查找().点击().随机延时(1,2)
        Field(zhuagui_assets.主界面_抓鬼文字).查找().偏移点击(0,0,350, 114).随机延时(1,2)

@sm.state(common_assets.活动界面)
def _(context):
    if context["action"] == "接取任务":
        field = Field(zhuagui_assets.活动弹框_抓鬼任务).查找()
        if field.是否找到():
            Field(common_assets.通用_活动界面未完成参加按钮).设置查找区域(
                {"x": field.x, "y": field.y, "w": 448, "h": 137}
            ).查找().点击().随机延时(1, 2)

@sm.state(common_assets.便捷组队弹框界面)
def _(context):
    if context["action"] == "接取任务":
        Field(common_assets.通用_创建队伍).查找().点击().随机延时(1, 2)

@sm.state(common_assets.队伍弹框界面)
def _(context):
    if context["action"] == "接取任务":
        if not context["是否已选择完队伍等级"]:
            # 选择等级按钮
            Field(common_assets.队伍弹框界面).查找().点击(1491, 146, 58, 53).随机延时(2, 3)
            

        elif Field(common_assets.队伍没满).查找().是否找到():
            # 一键喊话
            Field(common_assets.队伍弹框界面).查找().点击(1628, 953, 261, 72).随机延时(2, 3)

            # 选择世界频道
            Field(common_assets.队伍弹框界面).查找().点击(1641, 693, 232, 96).随机延时(2, 3)
        else:
            #关掉
            Field(common_assets.队伍弹框界面).查找().点击(1866, 35, 61, 62).随机延时(2, 3)
            
        
@sm.state(common_assets.调整组队等级界面)
def _(context):
    if context["action"] == "接取任务":

        # 70-89
        Field(common_assets.调整组队等级界面).查找().点击(1516, 467, 112, 54).随机延时(2, 3)

        # 1-69    
        Field(common_assets.调整组队等级界面).查找().点击(1383, 467, 114, 53).随机延时(2, 3)

        # 90-115
        # 随机ADB点击(1646, 466, 116, 52)
        # 随机延时(2, 3)

        # 确定按钮
        if Field(common_assets.调整组队等级界面).查找().点击(1086, 948, 230, 67).随机延时(2, 3).是否找到():
            context["是否已选择完队伍等级"] = True
        
@sm.state(common_assets.战斗界面)
def _(context):
    Field(common_assets.准备战斗).查找().点击(2210, 935, 79, 76)

@sm.state(common_assets.继续抓鬼提示)
def _(context):
    Field(common_assets.提示_关闭).查找().点击().随机延时(1, 2)

@sm.state(common_assets.缺人自动匹配提示)
def _(context):
    Field(common_assets.提示_关闭).查找().点击().随机延时(1, 2)

@sm.state(common_assets.队伍缺辅助)
def _(context):
    随机ADB点击(935, 642, 205, 65)
    随机延时(1, 2)
















if __name__ == "__main__":
    # result = sm.start()
    # Field(common_assets.主界面_未选中任务).查找().点击().随机延时(1,2)
    Field(common_assets.活动界面).查找().是否找到()




# 在哪个界面,就做哪些事


# 1.先定义界面，再定义状态：把游戏中所有可能的界面都列出来
# 2.制作界面特征模板：为每个界面制作图像识别模板
# 3.状态机只负责识别和切换：不处理复杂业务逻辑
# 4.使用上下文管理任务进度：状态之间通过上下文共享信息




# 在逻辑处理中,出现任何新界面,会干扰当前界面的逻辑进行的,都需要写一个新界面状态,例如队伍界面进行调整队伍等级,会出现队伍等级界面,这个队伍等级界面就用新的状态来注册

# 开始接取任务

# 主界面   点击活动

# 活动界面   点击参加抓鬼

# 便捷组队弹框界面   点击创建队伍

# 队伍界面  选择队伍等级

# 队伍等级调整界面   调整队伍等级, 关闭

# 队伍界面  满人关闭, 不满人喊话

# 主界面钟馗对话  点击抓鬼按钮

# 可能出现提示队伍问题界面  出现就关闭

# 这个时候就已经接取了任务, 但是停留在主界面不动

# 主界面,未切换任务面板     切换到任务面板

# 主界面,找到抓鬼任务     点击抓鬼任务

# 自动进行抓鬼任务了

# 战斗界面,未选择自动战斗    切换自动战斗

# 战斗失败了, 进行组队,再次点击开始