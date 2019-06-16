import re
from django import http
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
# Create your views here.
from apps.users.models import User
import logging
# 创建logger实例,并取个名字叫'Django'
logger = logging.getLogger('Django')


class RegisterView(View):

    """
    1.用户名需要分析是否重复(这里需要一个视图)
        用户名的长度有5-20个的要求
    2.密码 有长度的限制 8-20个,要求为数字,字母,_
    3.确认密码 和密码一致
    4.手机号 手机号得先满足规则
        再判断手机号是否重复
    5.图片验证码是一个后端功能
        图片验证码是为了防止 计算开攻击我们发送短信的功能
    6.短信发送
    7.必须同意协议
    8.注册也是一个功能

    必须要和后端交互的是:
    1.用户名/手机号是否重复
    2.图片验证码
    3.短信
    4.注册功能
    """

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """
        1.接收前端提交的用户名,密码和手机号
            这里注意前端以form表单形式提交,因此为post请求,
            数据采用request.POST来接收
        2.数据的验证,
            2.1 验证必传(必须要让前端传递给后端)的数据是否有值
            2.2 判断用户名是否符合规则
            2.3 判断密码是否符合规则
            2.4 判断确认密码和密码是否一致
            2.5 判断手机号是否符合规则
        3.验证数据没有问题的话可以进行入库操作
        4.返回响应给浏览器
        :param request:
        :return:
        """
        # 1.接收POST请求提交上来的数据
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')
        mobile = data.get('mobile')
        allow = data.get('allow')

        # 2.数据的验证,先验证是否有空的,再逐个验证是否有效
        if not all([username, password, password2, mobile]):
            return http.HttpResponseBadRequest('参数有问题!')
        if not re.match(r'[0-9a-zA-Z_]{5,20}', username):
            print('雷猴')
            return http.HttpResponseBadRequest('用户名不合法!')
        if not re.match(r'[0-9a-zA-Z_]{8,20}', password):
            return http.HttpResponseBadRequest('密码不合法')
        if password2 != password:
            return http.HttpResponseBadRequest('密码不合法')
        if not re.match(r'1[3-9]\d{9}', mobile):
            return http.HttpResponseBadRequest('密码不合法')
        if not allow:
            return http.HttpResponseBadRequest('请勾选用户同意协议')

        # 3.验证无误进行数据入库
            # 如果直接使用create入库,那么密码为明文.所以这里使用
            # django自带create_user进行入库,密码为密文
        # 注意:当我们操作外界资源(mysql,redis,file)时,最好进行try except的异常处理
        try:
            user = User.objects.create_user(username=username, password=password, moble=mobile)
        except Exception as e:
            # 这里如果有异常,我们使用日志对这个异常进行记录
            # 使用logger对象调用error错误方法,记录当前的异常(或者错误)
            logger.error(e)
            # 这里给html传递一个变量content,便可以通过模板语言if动态的显示数据异常
            content = {'error_message': '数据库异常!'}
            return render(request, 'register.html', content)
            return http.HttpResponseBadRequest('数据库异常!')

        # 4.返回响应
        # return http.HttpResponse('注册成功!')
        # 这里如果注册成功的话,可以直接进行重定向,定向到商城首页,
        # 因此需要创建子应用,包含首页视图函数
        # 4.返回响应(通过重定向到首页的方式返回给浏览器)

        # 注册完成之后,默认用户已经登录,需要保持登录的状态,这里可以使用session或者cookie
        # 本次使用session,自己实现的话使用,request.session

        # 系统也能自己去帮我们实现 登录状态的保持
        from django.contrib.auth import login
        login(request, user)

        path = reverse('contents:index')
        return redirect(path)


# 用户输入用户名后判断是否重复
"""
# 开发思路:
    前端:失去焦点之后,发送一个ajax请求,这个请求包含 用户名
    后端:接收数据,在数据库中查询用户名是否存在
    
    详细思路:
    1.用户输入用户名,当光标离开输入区时,前端发送异步ajax请求给后端
       1.1.这个请求包含 用户名
    2.后端接收前端发来的请求,并在数据库中进行查询,判断用户名是否重复
       确定请求方式和路由(敏感数据推荐使用POST):
       2.1.设置前端请求方式为查询字符串方式  usernames/***/count/
       2.2.使用关键字参数的路由进行正则匹配,匹配后引导至用户判断视图函数
       2.3.由于用户名非敏感信息,故采用get请求方式
    3.判断完成后将想用返回给前端(前端发送ajax请求,所以返回响应为JsonResponse响应方式)
"""


class UsernameCountView(View):

    def get(self, request, username):
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '数据库异常!'})
        if count == 0:
            return http.JsonResponse({'code': 0, 'count': count})
        else:
            return http.JsonResponse({'code': 400, 'errmsg': '用户名重复!'})


# 用户登录


"""
一.把大体思路写下来(前端需要收集什么,后端需要做什么)
    当用户把用户名/手机号 和密码填写完成之后,发送给后端
    后端验证用户名和密码

二.把大体思路写下来(后端的大体思路)
    1.后端需要接收数据
    2.验证数据
    3.如果验证成功则登录,如果不成功则失败

三.把详细思路完善一下(纯后端)
    1.后端需要接收数据(username,password)
    2.判断参数是否齐全,有没有空值
    3.判断用户名是否符合规则
    4.判断密码是否符合规则
    5.验证用户名和密码
    6.如果成功则登录, 即状态保持
    7.如果验证不成功则提示,用户名或密码错误

四.确定请求方式和路由
    POST    login/
"""


class LoginView(View):
    def get(self, request):

        return render(request, 'login.html')

    def post(self, request):

        # 1.后端需要接收数据(username,password)
        username = request.POST.get('username')
        password = request.POST.get('password')
        # 接收用户是否点击了记住登录的按钮,这个按钮属性名为 name="remembered"
        remembered = request.POST.get('remembered')

        # 2.判断参数是否齐全,有没有空值
        if not all([username, password]):
            return http.HttpResponseBadRequest('缺少必要的参数')

        # 3.判断用户名是否符合规则
        if not re.match(r'^[0-9a-zA-Z_]{5,20}$', username):
            return http.HttpResponseBadRequest('用户名不符合规则')

        # 4.判断密码是否符合规则
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseBadRequest('密码不符合规则')

        # 5.验证用户名和密码
        # 验证有两种方式:
        # ① 使用django自带的认证后端方法(authenticate)
        # ② 自己查询数据库(根据username查对应的user,再比对password)

        from django.contrib.auth import authenticate
        # 默认的认证后端是调用了from django.contrib.auth.backends import ModelBackend
        # ModelBcakend 中的认证方法
        # 如果用户名和密码正确,则返回用户对象 user
        user = authenticate(username=username, password=password)

        # 6.如果成功则登录, 即状态保持
        if user is not None:
            # 使用系统自带的 登陆成功后状态保持方法 login(request, user) 即设置session
            # todo 重要: login方法就是将登录信息保存在session里面
            login(request, user)

            if remembered == 'on':
                # 记住登录并且重新设置session有效期
                # request.session.set_expiry(secondes)
                request.session.set_expiry(30*24*3600)
            else:
                request.session.set_expiry(0)

            # 登录成功跳转到首页
            # return redirect(reverse('contents:index'))
            response = redirect(reverse('contents:index'))
            # todo 这里的cookie 值是user.username 还是 username ???
            response.set_cookie('username', username, 14*24*3600)
            return response
        # 7.如果验证不成功则提示,用户名或密码错误
        else:
            content = {'account_errmsg': '用户名或密码错误!'}
            return render(request, 'login.html', content)


"""
需求:
    用户点击退出,就把登陆信息删除
    由于登陆信息是保存在session里面的,所以这里删除掉session即可!
"""


# 定义退出的视图
class LogoutView(View):
    def get(self, request):

        # request.session.flush()
        # 系统提供了退出的方法
        from django.contrib.auth import logout

        logout(request)

        # 退出之后要跳转到指定页面
        # 这里设置为跳转到首页
        # 需要额外珊瑚粗cookie中的name, 因为首页的用户信息展示是通过username来判断的
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')

        return response


# 定义用户中心的视图

# 用户中心必须是登陆过的用户才可以访问,当前问题是没有登陆也显示了
# todo 重要:------------------------------------------------------------------------
# 因此增加LoginRequiredMixin来判断验证,即当没有获取到相应的登陆信息后,会跳转到指定的url里面去.
# 所以要想跳转到我们想指定去的地方,需要在setting.py里面修改这个默认的路由路径,即: LOGIN_URL = '/login/'
from django.contrib.auth.mixins import LoginRequiredMixin


class UserCenterInfoView(LoginRequiredMixin, View):
    def get(self, request):

        return render(request, 'user_center_info.html')
