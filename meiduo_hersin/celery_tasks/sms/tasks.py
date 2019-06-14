# 3.设置生产者 生产任务 task
#     ① 任务的本质就是函数
#     ② 这个函数必须要被celery的实例对象的 task装饰器装饰
#     ③ 必须调用celery 实例对象的自动检测来检测任务
from libs.yuntongxun.sms import CCP
from celery_tasks.main import app


@app.task
def send_sms_code(mobile, sms_code):

    CCP().send_template_sms(mobile, [sms_code, 5], 1)
