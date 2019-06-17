from django import http
from django.shortcuts import render

# Create your views here
from django.views import View

"""
1.实现登录界面 QQ 按钮的跳转
    ① 直接把拼接号的url放在a标签上面 https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=test
    ② 可以通过让前端发送一个ajax请求
"""


class QQAuthUserView(View):

    def get(self, request):

        return http.JsonResponse({'login_url': 'https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=test'})
