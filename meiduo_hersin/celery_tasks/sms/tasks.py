# 3.设置生产者 生产任务 task
#     ① 任务的本质就是函数
#     ② 这个函数必须要被celery的实例对象的 task装饰器装饰
#     ③ 必须调用celery 实例对象的自动检测来检测任务
from libs.yuntongxun.sms import CCP
from celery_tasks.main import app


"""
bind = True
第一参数是将始终是任务实例(self)
default_retry_delay 默认每次重试间隔的时间
"""


@app.task(bind=True,default_retry_delay=5)
def send_sms_code(self,mobile,sms_code):

    try:
        result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    except Exception as e:
        raise self.retry(exc=e,max_retries=10)

    if result != 0:
        # 不是0 都是失败 ,失败就应该重试
        raise self.retry(exc=Exception('baby,just check your configuration parameter!!!'),max_retries=3)


# @app.task(bind=True, default_retry_delay=5)
# def send_sms_code(self, mobile, sms_code):
#
#     try:
#         result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
#     except Exception as e:
#         raise self.retry(exc=e, max_retries=10)
#     if result != 0:
#         # 不是0都是失败,失败就应该重试
#         # 这里最大重试次数设定为10次
#         raise self.retry(exc=Exception('baby,just check your configuration parameter!!!'), max_retries=3)
