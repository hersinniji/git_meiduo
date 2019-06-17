from QQLoginTool.QQtool import OAuthQQ
from django import http
from django.shortcuts import render

# Create your views here
from django.views import View

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
        return render(request, 'oauth_callback.html')


