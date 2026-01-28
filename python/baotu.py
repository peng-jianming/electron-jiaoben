from tools import TaskLineMachine


def create_baotu_task(device_id):
    sm = TaskLineMachine(device_id)

    @sm.state("活动界面")
    def _(context, 界面):
        # 简化写法：点击如果找到，未找到则停止
        if not 界面.按钮.宝图任务.点击如果找到(日志='点击参加'):
            sm.stop()

    @sm.state("战斗界面")
    def _(context, 界面):
        # 简化写法：查找并点击
        界面.状态.未自动战斗.点击如果找到(日志='点击未准备战斗按钮')

    @sm.state("主界面")
    def _(context, 界面):
        # 简化写法：使用 or 链实现"找到就返回"的逻辑
        (界面.按钮.对话框第一个选项按钮.点击如果找到(日志='点击店小二对话的听听无妨按钮') or
         界面.状态.是否未选中任务栏.点击如果找到(日志='选中任务栏') or
         界面.按钮.任务面板_宝图文字.点击如果找到(日志='点击任务面板的宝图任务文字') or
         界面.按钮.活动.必须点击(日志='点击活动按钮'))

    return sm
