# 用来定义一个视图函数,让它继承自LoginRequiredMixin,并重写LoginRequiredMixin的方法
from django.contrib.auth.mixins import LoginRequiredMixin
from django import http

from apps.users import utils
from utils.response_code import RETCODE


class LoginRequiredJSONMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '您未登录'})