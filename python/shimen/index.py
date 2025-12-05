from tools.StateMachine import StateMachine
from tools.Field import Field
from resource.index import ms


sm = StateMachine()

@sm.state("回到主界面")
def _():
    return "打开活动界面"


@sm.state("打开活动界面")
def _():
    Field(ms["通用_主界面活动按钮"]).查找().点击().随机延时(1, 2)
    return (
        "打开师门界面"
        if Field(ms["通用_活动界面"]).查找().是否找到()
        else "回到主界面"
    )


@sm.state("打开师门界面")
def _():
    field = Field(ms["活动界面师门任务"]).查找()
    if not field.是否找到():
        return "回到主界面"
    
    Field(ms["活动界面参加按钮"]).设置查找区域(
        {"x": field.x, "y": field.y, "w": 450, "h": 130}
    ).查找().点击().随机延时(1, 2)
    
    return (
        "接取师门任务" if Field(ms["师门界面"]).查找().是否找到() else "回到主界面"
    )


@sm.state("接取师门任务")
def _():
    if Field(ms["师门界面继续任务按钮"]).查找().点击().随机延时(1, 2).是否找到():
        return "做师门任务"
    if Field(ms["师门界面去完成按钮"]).查找().点击().随机延时(1, 2).是否找到():
        return "做师门任务"
    if Field(ms["师门界面选择按钮"]).查找().点击().随机延时(1, 2).是否找到():
        return "做师门任务"
    
    Field(ms["关闭师门弹框"]).查找().点击().随机延时(1, 2)
    return "结束"


@sm.state("做师门任务")
def _():
   sm2 = StateMachine()
   @sm2.state("1")
   def _():
       return '1' if Field(ms["通用_跳过"]).查找().点击(300, 300, 2000, 980).随机延时(1, 2).是否找到() else '2'
   @sm2.state("2")
   def _():
       return '1' if Field(ms["通用_使用"]).查找().点击().随机延时(1, 2).是否找到() else '3'
   @sm2.state("3")
   def _():
       return "1" if Field(ms["通用_上交"]).查找().点击().随机延时(1, 2).是否找到() else '4'
   @sm2.state("4")
   def _():
       return '1' if Field(ms["弹框_购买"]).查找().点击().随机延时(1, 2).是否找到() else '5'
   @sm2.state("5")
   def _():
       return '1' if Field(ms["摆摊弹框_购买"]).查找().点击().随机延时(1, 2).是否找到() else '6'
   @sm2.state("6")
   def _():
       return "1" if Field(ms["对话选项框"]).查找().偏移点击(40, 120, 400, 60).随机延时(1, 2).是否找到() else '7'
   @sm2.state("7")
   def _():
       return "1" if Field(ms["对话说话框"]).查找().点击(300, 300, 1800, 600).随机延时(1, 2).是否找到() else '8'
   @sm2.state("8")
   def _():
       return "1" if Field(ms["主界面_师门文字"]).查找().偏移点击(0, 0, 336, 121).随机延时(1, 2).是否找到() else '9'
   @sm2.state("9")
   def _():
       if Field(ms["师门_任务完成弹框"]).查找().点击(1038, 802, 323, 68).随机延时(1, 2).是否找到():
        Field(ms["关闭师门弹框"]).查找().点击().随机延时(1, 2)
        return "结束"

   sm2.start("1")
   return '结束'

if __name__ == "__main__":
    result = sm.start("回到主界面")
    print(f"状态机执行完成，返回结果: '{result}'")