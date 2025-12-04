from stateMachine import StateMachine
from Field import Field


# 使用示例
if __name__ == "__main__":

    def aaa():
        print("aaaa")
        ccc = Field(
            {
                "标识": "测试1",
                "方式": "opencv找图",
                "图片路径": "./shimenjiemian.png",
            }
        ).查找().点击().是否找到()

        return '2' if ccc else '1'

    def bbb():
        print("bbbb")
        ccc = Field(
            {
                "标识": "测试2",
                "方式": "opencv找图",
                "图片路径": "./shimenjiemian.png",
            }
        ).查找().点击().是否找到()
        return '3' if ccc else '1'

    def ccc():
        print("cccc")

        return '4'

    result = StateMachine().on("1", aaa).on("2", bbb).on("3", ccc).start("1")
    # 启动状态机，开始时代码会在这里"暂停"直到状态机执行完毕

    # 状态机执行完毕后，代码继续往下执行
    print(f"状态机执行完成，返回结果: '{result}'")
    print("代码继续执行...")
