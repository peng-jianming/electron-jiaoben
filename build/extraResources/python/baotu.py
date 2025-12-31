from index import DeviceController, Field, TaskLineMachine
from resource.assets import config as 配置



class Baotu(DeviceController):
    def __init__(self, device_id):
        super().__init__(device_id)

    def start(self):
        sm = TaskLineMachine(self)

        @sm.state(配置.活动界面)
        def _(context):
            if not Field(配置.活动界面['按钮']['宝图任务'], self).设置标识('点击参加').查找().偏移点击(*配置.活动界面['按钮']['宝图任务']['偏移点击区域']).随机延时(1, 3).是否找到():
                sm.stop()



        @sm.state(配置.战斗界面)
        def _(context):
            Field(配置.战斗界面['状态']['是否未准备战斗'], self).设置标识('点击未准备战斗按钮').查找().点击(*配置.战斗界面['按钮']['未准备战斗']).随机延时(1, 3)




        @sm.state(配置.主界面)
        def _(context):
                if Field(配置.主界面_店小二对话, self).设置标识('点击店小二对话的听听无妨按钮').查找().点击(*配置.主界面_店小二对话['按钮']['听听无妨']).随机延时(1, 3).是否找到():
                    return
                
                if Field(配置.主界面['状态']['是否未选中任务栏'], self).设置标识('选中任务栏').查找().点击().随机延时(1, 3).是否找到():
                    return

                if Field(配置.主界面_宝图文字, self).设置标识('点击任务面板的宝图任务文字').查找().偏移点击(*配置.主界面_宝图文字['偏移点击区域']).随机延时(1, 3).是否找到():
                    return

                Field(配置.主界面, self).设置标识('点击活动按钮').查找().点击(*配置.主界面["按钮"]["活动"]).随机延时(1, 3)


        sm.start()









if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Python Server")
    parser.add_argument("--ids", type=str, default='', help="The id number.")
    args = parser.parse_args()
    arr = args.ids.split(',')
    for device_id in arr:
        baotu = Baotu(device_id)
        baotu.start()
        print(f"设备 {device_id} 宝图任务结束")



