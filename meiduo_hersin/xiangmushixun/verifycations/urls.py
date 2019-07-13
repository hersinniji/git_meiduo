from django.conf.urls import url
from . import views
import uuid

urlpatterns = [
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view()),
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SmsCodeView.as_view()),
    # 找回密码第一步
    url(r'^accounts/(?P<username>\w+)/sms/token/$', views.PwdCodeView.as_view()),
    # 找回密码第二步发送短信
    url(r'^sms_codes/$', views.PwdSMSCodeView.as_view()),
    # 找回密码第二步
    url(r'^accounts/(?P<username>\w+)/password/token/$', views.PwdCheckCodeView.as_view()),
]
