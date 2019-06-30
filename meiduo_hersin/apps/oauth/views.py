import re

from QQLoginTool.QQtool import OAuthQQ

from django import http
from django.contrib.auth import login
from django.shortcuts import render, redirect

# Create your views here
from django.urls import reverse
from django.views import View

from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import generate_access_token, check_access_token
from apps.users.models import User
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
        """Oauth2.0认证"""

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
qq登录成功之后页面跳转

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
            openid_access_token = generate_access_token(openid)
            context = {'openid_access_token': openid_access_token}
            return render(request, 'oauth_callback.html', context)
        else:
            # ② 查询到记录存在
            path = reverse('contents:index')
            response = redirect(path)

            # 登录状态保持
            login(request, qquser.user)

            # next = request.GET.get('state')
            # response = redirect(next)

            # 设置cookie信息,登录时用户名写入到cookie，有效期为14天
            response.set_cookie('username', qquser.user.username, max_age=14 * 24 * 3600)

            return response

    """
    通过post方法来绑定openid和用户信息

    1.接收数据
    2.获取数据
    3.校验参数
    4.openid解密
    5.根据手机号进行用户信息的判断
        5.1 如果手机号之前注册过，但没绑定过，则和当前这个用户进行绑定，绑定前要验证密码
        5.2 如果此手机号之前没注册过，则重新创建用户，并和当前的openid进行绑定
    6.设置登录的状态
    7.设置cookie信息
    8.跳转指定
    """

    def post(self, request):
        """绑定openid和用户信息"""

        # 1.接收数据
        data = request.POST

        # 2.获取数据
        mobile = data.get('mobile')
        password = data.get('pwd')
        sms_code_client = data.get('sms_code')
        access_token = data.get('access_token')

        # 3.校验参数(参数是否有空值、参数格式是否正确)
        # 判断参数是否齐全
        if not all([mobile, password, sms_code_client, access_token]):
            return http.HttpResponseBadRequest('缺少必传参数')

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseBadRequest('请输入正确的手机号码')

        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseBadRequest('请输入8-20位的密码')

        # # 判断短信验证码是否一致
        # """
        # """
        # # 检测openid是否有效
        # """
        # """
        # # 保存注册数据（保存到用户表）
        # user = User.objects.get

        # 4.openid解密
        openid = check_access_token(access_token)

        # 5.根据手机号进行用户信息的判断
        try:
            user = User.objects.get(moble=mobile)

        # 5.1 如果此手机号之前没注册过，则重新创建用户，并和当前的openid进行绑定
        except Exception as e:
            user = User.objects.create(
                moble=mobile,
                password=password
            )

        # 5.2 如果手机号之前注册过，但没绑定过，则和当前这个用户进行绑定，绑定前要验证密码
        else:
            if not user.check_password(password):
                return http.HttpResponseBadRequest('密码错误！')

        OAuthQQUser.objects.create(
            openid=openid,
            user=user
        )

        # 6.设置登录的状态
        login(request, user)

        # 7.设置cookie信息
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=14*24*3600)

        # 8.跳转指定
        return response



#
# # ###########################itadangerous的加密使用##################################
#
# # 1.导入
# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# from meiduo_hersin import settings
#
# # 2.创建实例对象
# # secret_key   秘钥   习惯上使用settings文件中的settings,secret_key
# # expire_in      过期时间      单位是秒
# s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
#
# # 3.组织要加密的数据
# script = {
#     'openid': '1234'
# }
#
# # 4.加密
# s.dumps(script)
#
# # ###########################itadangerous的解密使用##################################
# # 解密所需要的秘钥和时间是一样的
#
# # 1.导入
# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# from meiduo_hersin import settings
#
# # 2.创建实例对象
# # secret_key   秘钥   习惯上使用settings文件中的settings,secret_key
# # expire_in      过期时间      单位是秒
# s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
#
# # 3.解密
# s.loads('要解密的数据')

# 加密之后的数据为二进制数，解密时可以直接对这个二进制数或者二进制转换后的数进行解密处理
# >>> a = s.dumps(script)
# >>> a
# b'eyJhbGciOiJIUzUxMiIsImV4cCI6MTU2MDg1MzMxMCwiaWF0IjoxNTYwODQ5NzEwfQ.eyJvcGVuaWQiOiIxMjM0In0.nP9cVbmoUHCg9iHuTvXsBnzw-jqgF1KWCHGTfErpIwNfg9BvpKeP5b2_35EjOy9Gx6W171XhlCvPYRJfjc-mew'
# >>> b = a.decode()
# >>> b
# 'eyJhbGciOiJIUzUxMiIsImV4cCI6MTU2MDg1MzMxMCwiaWF0IjoxNTYwODQ5NzEwfQ.eyJvcGVuaWQiOiIxMjM0In0.nP9cVbmoUHCg9iHuTvXsBnzw-jqgF1KWCHGTfErpIwNfg9BvpKeP5b2_35EjOy9Gx6W171XhlCvPYRJfjc-mew'
# >>> s.loads(a)
# {'openid': '1234'}
# >>> s.loads(b)
# {'openid': '1234'}
# >>>
