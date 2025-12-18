import sys
import os

# 将父目录添加到 Python 路径，以便能找到 common 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index import Field, 随机ADB点击, ADB点击, 随机延时
from common.assets import config as common_assets
from common.index import StateMachine
from zhuagui.assets import config as zhuagui_assets

sm = StateMachine()

def 识别屏幕(url):
  if Field(common_assets.继续抓鬼提示).设置大图路径(url).查找().是否找到():
    return Field(common_assets.提示_关闭).查找().点击().随机延时(1, 2)
  if Field(common_assets.缺人自动匹配提示).设置大图路径(url).查找().是否找到():
    return Field(common_assets.提示_关闭).查找().点击().随机延时(1, 2)

sm.设置屏幕识别函数(识别屏幕)

sm.update_context(action="接取任务")


@sm.state("主界面")
def _(context):
    
    if context["action"] == "接取任务":
        # 钟馗对话
        if(Field(zhuagui_assets.钟馗对话).查找().是否找到()):
            # 点击抓鬼任务
            随机ADB点击(1829, 361, 403, 66)
            context["action"] = "任务中"
            随机延时(2, 3)

        Field(common_assets.主界面活动按钮).查找().点击().随机延时(1, 2)

    if context["action"] == "任务中":
        Field(common_assets.主界面_未选中任务).查找().点击().随机延时(1,2)
        Field(zhuagui_assets.主界面_抓鬼文字).查找().偏移点击(0,0,350, 114).随机延时(1,2)

        
    

@sm.state("活动界面")
def _(context):
    if context["action"] == "接取任务":
        field = Field(zhuagui_assets.活动弹框_抓鬼任务).查找()
        if field.是否找到():
            Field(common_assets.通用_活动界面未完成参加按钮).设置查找区域(
                {"x": field.x, "y": field.y, "w": 448, "h": 137}
            ).查找().点击().随机延时(1, 2)

        

@sm.state("便捷组队弹框界面")
def _(context):
    if context["action"] == "接取任务":
        print("便捷组队弹框界面")
        Field(common_assets.通用_创建队伍).查找().点击().随机延时(1, 2)


是否已选择完队伍等级 = False
@sm.state("队伍弹框界面")
def _(context):
    if context["action"] == "接取任务":
        if not 是否已选择完队伍等级:
            # 选择等级按钮
            随机ADB点击(1491, 146, 58, 53)
            随机延时(2, 3)

        elif Field(common_assets.队伍没满).查找().是否找到():
            # 一键喊话
            随机ADB点击(1628, 953, 261, 72)
            随机延时(2, 3)

            # 选择世界频道
            随机ADB点击(1641, 693, 232, 96)
            随机延时(2, 3)
        else:
            #关掉
            随机ADB点击(1866, 35, 61, 62)
            随机延时(2, 3)
        
            

@sm.state("调整组队等级界面")
def _(context):
    global 是否已选择完队伍等级
    if context["action"] == "接取任务":

        # 70-89
        随机ADB点击(1516, 467, 112, 54)
        随机延时(2, 3)
        # 1-69    
        随机ADB点击(1383, 467, 114, 53)
        随机延时(2, 3)

        # 90-115
        # 随机ADB点击(1646, 466, 116, 52)
        # 随机延时(2, 3)

        # 确定按钮
        随机ADB点击(1086, 948, 230, 67)
        是否已选择完队伍等级 = True
        随机延时(2, 3)
        


if __name__ == "__main__":
    result = sm.start()


# 返回主界面
# 打开活动界面
# 点击参加抓鬼

# 有队伍 -> 前往钟馗处
# 没有队伍 -> 打开便捷组队界面

#


# 在主界面中, 点击活动按钮, 出现活动弹框, 在活动弹框中,找到抓鬼任务中的参加按钮,此时,如果已有队伍,则自动前往钟馗处,否则自动打开便捷组队弹框,需要自己组满人,然后回到主界面,然后再次点击参加抓鬼,此时会自动前往钟馗处
# 在钟馗处,对话会出现抓鬼任务按钮,可以点击抓鬼任务,然后就会接取抓鬼任务,自动关闭对话,然后就会自动接取任务做任务,此时主界面右侧任务栏会出现抓鬼任务轮数提示,
# 在自动做任务中,就是不断的自动寻路和进入抓鬼战斗界面,当全部完成,就会站在原地不动,需要再次按照接取任务的思路进行接取任务


# 在哪个界面,就做哪些事


# 一个状态 = 一个游戏界面/场景

# 状态切换 = 界面切换, 如果界面切换不符合预期,则返回主界面,重新接取任务

# 每个状态只处理当前界面的操作

# 状态之间通过上下文（context）传递信息


# 1.先定义界面，再定义状态：把游戏中所有可能的界面都列出来
# 2.制作界面特征模板：为每个界面制作图像识别模板
# 3.状态机只负责识别和切换：不处理复杂业务逻辑
# 4.使用上下文管理任务进度：状态之间通过上下文共享信息
