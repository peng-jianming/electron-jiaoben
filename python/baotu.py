from resource.assets import config as 配置
from tools import TaskLineMachine


def create_baotu_task(device_id):
    sm = TaskLineMachine(device_id)

    @sm.state(配置.活动界面)
    def _(context):
        if not sm.Field(配置.活动界面['按钮']['宝图任务']).设置标识('点击参加').查找().偏移点击(*配置.活动界面['按钮']['宝图任务']['偏移点击区域']).随机延时(1, 3).是否找到():
            sm.stop()

    @sm.state(配置.战斗界面)
    def _(context):
        sm.Field(配置.战斗界面['状态']['是否未准备战斗']).设置标识('点击未准备战斗按钮').查找().点击(*配置.战斗界面['按钮']['未准备战斗']).随机延时(1, 3)

    @sm.state(配置.主界面)
    def _(context):
        if sm.Field(配置.主界面_店小二对话['按钮']['听听无妨']).设置标识('点击店小二对话的听听无妨按钮').查找().点击().随机延时(1, 3).是否找到():
            return
        
        if sm.Field(配置.主界面['状态']['是否未选中任务栏']).设置标识('选中任务栏').查找().点击().随机延时(1, 3).是否找到():
            return

        if sm.Field(配置.主界面_宝图文字).设置标识('点击任务面板的宝图任务文字').查找().偏移点击(*配置.主界面_宝图文字['偏移点击区域']).随机延时(1, 3).是否找到():
            return

        sm.Field(配置.主界面).设置标识('点击活动按钮').查找().点击(*配置.主界面["按钮"]["活动"]).随机延时(1, 3)

    return sm
