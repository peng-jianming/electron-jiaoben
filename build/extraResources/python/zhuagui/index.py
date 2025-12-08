import sys
import os

# 将父目录添加到 Python 路径，以便能找到 common 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.index import StateMachine, Field
from common.assets import config as common_assets
from zhuagui.assets import config as zhuagui_assets

sm = StateMachine()

# @sm.state("回到主界面")
# def _():
#     return "打开活动界面"

# @sm.state("打开活动界面")
# def _():
#     Field(common_assets.通用_主界面活动按钮).查找().点击().随机延时(1, 2)
#     return (
#         "参加抓鬼"
#         if Field(common_assets.通用_活动界面).查找().是否找到()
#         else "回到主界面"
#     )

# @sm.state("参加抓鬼,匹配组队")
# def _():
#     field = Field(zhuagui_assets.活动弹框_抓鬼任务).查找()
#     if field.是否找到():
#         Field(common_assets.通用_活动界面未完成参加按钮).设置查找区域({'x': field.x, 'y': field.y, 'w': 448, 'h': 137}).查找().点击().随机延时(1,2)
#         Field(zhuagui_assets.便捷组队弹框_自动匹配).查找().点击().随机延时(1,2)
#         if Field(zhuagui_assets.便捷组队弹框_取消匹配).查找().是否找到():
#             return '抓鬼任务中'
        
#     return '回到主界面'








@sm.state("主界面")
def _():
    # 1.点击活动按钮

    # 2.正在做抓鬼任务

    # 3.
    1

@sm.state("活动弹框界面")
def _():
    1

@sm.state("便捷组队弹框界面")
def _():
    1

@sm.state("队伍弹框界面")
def _():
    1

@sm.state("对话弹框界面")
def _():
    1

@sm.state("战斗界面")
def _():
    1


if __name__ == "__main__":
    print( "开始")
    result = sm.start("回到主界面")
    print(f"状态机执行完成，返回结果: '{result}'")





# 返回主界面
# 打开活动界面
# 点击参加抓鬼

# 有队伍 -> 前往钟馗处
# 没有队伍 -> 打开便捷组队界面

# 


# 在主界面中, 点击活动按钮, 出现活动弹框, 在活动弹框中,找到抓鬼任务中的参加按钮,此时,如果已有队伍,则自动前往钟馗处,否则自动打开便捷组队弹框,需要自己组满人,然后回到主界面,然后再次点击参加抓鬼,此时会自动前往钟馗处
# 在钟馗处,对话会出现抓鬼任务按钮,可以点击抓鬼任务,然后就会接取抓鬼任务,自动关闭对话,然后就会自动开始做任务,此时主界面右侧任务栏会出现抓鬼任务轮数提示,
# 在自动做任务中,就是不断的自动寻路和进入抓鬼战斗界面,当全部完成,就会站在原地不动,需要再次按照开始的思路进行接取任务

















# 在哪个界面,就做哪些事



# 一个状态 = 一个游戏界面/场景

# 状态切换 = 界面切换, 如果界面切换不符合预期,则返回主界面,重新开始

# 每个状态只处理当前界面的操作

# 状态之间通过上下文（context）传递信息


# 1.先定义界面，再定义状态：把游戏中所有可能的界面都列出来
# 2.制作界面特征模板：为每个界面制作图像识别模板
# 3.状态机只负责识别和切换：不处理复杂业务逻辑
# 4.使用上下文管理任务进度：状态之间通过上下文共享信息