from QQLoginTool.QQtool import OAuthQQ
from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Create your views here
from django.urls import reverse
from django.views import View

from apps.oauth.models import OAuthQQUser
from meiduo_hersin import settings

"""
1.拼接用户跳转的url，当用户同意登录之后，会生成code
2.通过code换取token
3.通过token换取openid
4.绑定用户

"""


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


"""
一 把需求写下来（前端需要做什么，后端需要做什么）
    前端需要把用户同意的code(code是认证服务器返回的)提交给后端
    后端通过code换取token

二 把大体思路写下来（后端的大体思路）
    1.获取code
    2.通过读取文档将code转换为token
    
三 把详细思路完善一下（纯后端）

四 确定我们请求的方式和路由
    GET    oauth_callback
    
"""


class OauthQQUserView(View):

    def get(self, request):

        # 1.获取code
        code = request.GET.get('code')
        if code is None:
            return render(request, 'oauth_callback.html', context={'errmsg': '没有获取到指定参数'})

        # 2.通过读取文档将code转换为token
        qqoauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
        )

        # 这里通过调用get_access_token方法，函数内部自动将code、client_id、client_secret、redirect_uri
        # 几个信息拼接为路由，并进行访问，最终将响应数据进行转换和返回，返回值即为access_token
        token = qqoauth.get_access_token(code)
        # return render(request, 'oauth_callback.html')

        # openid是此网站上唯一对应用户身份的标识，网站可将此ID进行存储便于用户下次登录时辨识其身份
        # 或将其与用户在网站上的原有账号进行绑定。
        openid = qqoauth.get_open_id(token)

        # todo 获取到openid后需要做什么事情？？？
        """
        ① 通过openid查询记录，若记录存在，则实现状态保持，并重定向到首页
        ② 如果没有同样的openid，则引导到用户绑定界面，提示用户进行绑定（qq账号和meiduo商城账号）。
        """

        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # ① 查询到记录不存在
            # 在给前端返回这个绑定界面时，应该把openid也返回给前端，这样，当用户填写完成信息后，点击提交按钮
            # 可以将openid和用户信息一并传给后端，方便后端进行一一对应，并存储openid数据。
            # 不然的话，前端传递通过绑定界面传递给后端的信息没有openid，后端不知道该绑定谁
            return render(request, 'oauth_callback.html', context={'openid': openid})
        else:
            # ② 查询到记录存在
            response = redirect(reverse('contents:index'))
            # 登录状态保持
            login(request, qquser.user)
            # 设置cookie信息
            response.set_cookie('username', qquser.user.username, max_age=14*24*3600)
            return response
