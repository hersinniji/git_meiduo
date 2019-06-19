# 3.设置生产者 生产任务 task
#     ① 任务的本质就是函数
#     ② 这个函数必须要被celery的实例对象的 task装饰器装饰
#     ③ 必须调用celery 实例对象的自动检测来检测任务
from celery_tasks.main import app
from meiduo_hersin import settings


@app.task
def send_active_email(email):
    # 4.发送激活邮件
    from django.core.mail import send_mail

    # 编辑激活邮件的内容
    # subject 主题
    # message 发送的内容
    # from_email 发件人
    # recipient_list  收件人邮箱列表

    subject = '主题'
    message = '内容'
    from_email = settings.EMAIL_FROM
    recipient_list = [email]
    html_message = '<h1>你好,王佳星!</h1><br><h2>欢迎来到美多商城!</h2><br>'

    # 能够发送邮件给用户的邮箱
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        html_message=html_message
    )
