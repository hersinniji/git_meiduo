"""
伪代码,说明问题
"""


# 1.定义队列类,创建空的任务队列
class Broker(object):
    # 任务队列
    broker_list = []


# 2.定义消费者类,包含执行任务的方法
class Worker(object):
    # 任务执行者
    def run(self, broker, func):
        if func in broker.broker_list:
            func()
        else:
            return 'error'


# 3.定义任务函数,本次项目中,任务函数就是去执行发短信的功能
# 创建任务,任务就相当于一个函数,任务就是去发送短信
def send_sms_code():
    print('send_sms_code开始发送短信...')


# 4.创建celery(分布式任务队列)类
class Celery(object):
    # 4.1初始化一个broker,一个worker
    def __init__(self):
        self.broker = Broker()
        self.worker = Worker()

    # 4.2添加生产任务, 就是把 任务函数 增加到 任务列表(队列) 中去
    def add(self, func):
        self.broker.broker_list.append(func)

    # 4.3工作
    def work(self, func):
        self.worker.run(self.broker, func)


# 实例对象
app=Celery()
# 添加任务
app.add(send_sms_code)
# 消费者工作
app.work(send_sms_code)

