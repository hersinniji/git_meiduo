"""
生产者--task    任务队列--broker    消费者--worker
celery 将这三者串联起来

1.创建celery

2.设置队列 broker

3.设置生产者 生产任务 task
    ① 任务的本质就是函数
    ② 这个函数必须要被celery的实例对象的 task装饰器装饰
    ③ 必须调用celery 实例对象的自动检测来检测任务

4.设置消费者 worker
    celery -A Celery实例对象的文件 worker -l info

    celery -A celery_tasks.main worker -l info

"""


# celery有可能会用到django, 当django启动时加载应用程序,以便@shared_task装饰器将使用它
# ① 让celery去加载当前工程中的配置文件
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_hersin.settings")

# ②创建celery实例对象
from celery import Celery
# celery的第一个参数是main,习惯上填写当前脚本工程的工程名
# 给celery的实例起个名字,这个名字唯一就可以
app = Celery('celery_tasks')

# ③celery去设置任务队列broker
# config_from_object 参数: 就是配置文件的路径
app.config_from_object('celery_tasks.config')

# ④让celery自动检测任务
# autodiscover_tasks 的参数是一个列表.列表的元素是: 任务的包路径
app.autodiscover_tasks(['celery_tasks.sms'])
