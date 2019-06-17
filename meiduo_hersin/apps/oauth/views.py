from QQLoginTool.QQtool import OAuthQQ
from django import http
from django.shortcuts import render

# Create your views here
from django.views import View

from meiduo_hersin import settings

"""
1.实现登录界面 QQ 按钮的跳转
    方法① 直接把拼接号的url放在a标签上面 https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=test
    方法② 可以通过让前端发送一个ajax请求
    方法③ 使用QQ登录工具 QQLoginTool，可以通过输入参数自行拼接url
"""


class QQAuthUserView(View):

    def get(self, request):

        # 方法②
        # return http.JsonResponse({'login_url': 'https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101518219&redirect_uri=http://www.meiduo.site:8000/oauth_callback&state=test'})

        # 方法③
        # 1.创建实例对象
        state = 'test'
        qqoauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=state
        )

        # 2.调用方法
        login_url = qqoauth.get_qq_url()

        return http.JsonResponse({'login_url': login_url})
