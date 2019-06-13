import re
from django import http
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
