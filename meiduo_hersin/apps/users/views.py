import json
import re
from django import http
from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
# Create your views here.
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.users.models import User, Address
import logging
# 创建logger实例,并取个名字叫'Django'
from apps.users.utils import active_eamil_url, check_active_eamil_url
from celery_tasks.email.tasks import send_active_email
from meiduo_hersin import settings
from utils.response_code import RETCODE
from utils.views import LoginRequiredJSONMixin

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
            return http.HttpResponseBadRequest('手机号不合法')
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
            return http.HttpResponseBadRequest('绝对没出错')

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
        # todo ------------------------------------------------------------------------------
        # password = make_password(password, salt=None, hasher='default')
        # user = authenticate(username=username, password=password)
        user = User.objects.get(username=username)

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

            # 这里需要注意，由于loginRequireMixin的存在，如果之前已经登录过，访问了其他页面
            # 再次访问登录界面时，路径里面会自动增加next=/上次的访问页面/，所以这里需要进行判断
            # 如果有next参数，则跳转到指定页面
            # 如果没有，则跳转到首页
            next = request.GET.get('next')
            if next:
                response = redirect(next)
            else:
                response = redirect(reverse('contents:index'))

            # 登录成功跳转到首页
            # return redirect(reverse('contents:index'))
            # response = redirect(reverse('contents:index'))
            # todo 这里的cookie 值是user.username 还是 username ???
            response.set_cookie('username', username, 14*24*3600)
            print(request.user)
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


# 定义用户中心视图的思路
# 用户中心必须是登陆过的用户才可以访问,当前问题是没有登陆也显示了
# todo 重要:------------------------------------------------------------------------
# 因此增加LoginRequiredMixin来判断验证,即当没有获取到相应的登陆信息后,会跳转到指定的url里面去.
# 所以要想跳转到我们想指定去的地方,需要在setting.py里面修改这个默认的路由路径,即: LOGIN_URL = '/login/'

from django.contrib.auth.mixins import LoginRequiredMixin


# 定义用户中心的视图
class UserCenterInfoView(LoginRequiredMixin, View):

    def get(self, request):

        content = {
            'username': request.user.username,
            'mobile': request.user.moble,
            'email': request.user.email,
            'email_active': request.user.email_active

        }
        return render(request, 'user_center_info.html', content)


# 用户中心发送邮件思路
"""
一.把大体思路写下来(前端需要收集什么,后端需要做什么)
    前端 当用户把邮箱内容填写完成后,点击保存按钮需要收集用户的邮箱信息,然后发送一个sjax请求给后端
    
    后端 要接收数据,然后保存数据(更新用户邮箱数据),并发送激活邮件,用户一点击就可以激活
二.把大体思路写下来(后端的大体思路)
    1.接收邮箱数据
    2.验证邮箱数据
    3.保存数据
    4.发送激活邮件
    5.返回响应

三.把详细思路完善一下(纯后端)
    1.接收邮箱数据
    2.验证邮箱数据
    3.保存数据(更新指定用户的邮箱信息)
    4.发送激活邮件
        编辑激活邮件的内容
        能够发送邮件给用户的邮箱
    5.返回响应

四.确定请求方式和路由
    get     :一般是获取数据
    post    :一般是提交数据
    put     :一般是更新数据(提交的数据在请求body中)    emails/
    delete  :一般是删除数据
"""


# 1.因为这里接收的是ajax请求,ajax请求使用postman也可以发送,为防止黑客和匿名用户恶意访问
# 这里需要进行用户验证,验证内容为: 只有登录过的用户才可以访问发送邮件的接口.
# 2.验证登录的话视图函数需要继承LoginRequiredMixin,若视图函数继承...Mixin
# 当用户访问接口时,通过request.user判断用户是否已经登录
# 没登录(is_authenticate是false)的话直接重定向到登录界面
# 已登录则按照视图函数定义的响应走.
# 但是继承LoginRequiredMixin的话,默认会返回 登录的重定向
# 但是当前的视图是通过ajax来请求的,我们应该返回json数据,因此需要进行 重写
class EmailView(LoginRequiredJSONMixin, View):

    def get(self, request):

        # 1.接收邮箱数据
        data = json.loads(request.body.decode())
        email = data.get('email')

        # 2.验证邮箱数据
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据保存失败'})

        # 3.保存数据(更新指定用户的邮箱信息)
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据保存失败'})

        # 4.未使用celery,直接发送邮件
        """
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
            subject = subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message
        )
        """

        # 4.使用celery任务队列异步发动邮件
        # todo 切记不能忘了delay,不然不是异步发送!!!!!!
        verify_url = active_eamil_url(email, request.user.id)
        send_active_email.delay(email, verify_url)

        # 5.返回响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


# 激活邮件链接思路
"""
一.把大体思路写下来(前端需要收集什么,后端需要做什么)
    用户点击激活链接后.会跳转到指定界面.
    后端 通过路由中的参数获取用户的信息
二.把大体思路写下来(后端的大体思路)
    1.获取token
    2.解密token数据
    3.根据解密的数据查询用户
    4.修改email_active字段为1
    5.跳转到个人中心界面

三.把详细思路完善一下(纯后端)
    1.获取token数据是查询字符串的方式,使用request.GET去获取
    2.使用isdangerous去解密token
    3.根据解密的数据(user_id),查询用户信息
    4.修改用户的信息(email_active)
    5.跳转到个人中心

四.确定请求方式和路由
    get     email_active/
"""


# 激活邮件链接
class EmailActiveView(View):

    def get(self, request):

        # 1.获取token数据是查询字符串的方式, 使用request.GET去获取
        token = request.GET.get('token')
        if token is None:
            return http.HttpResponseBadRequest('缺少必要参数')

        # 2.使用is_dangerous去解密token
        user = check_active_eamil_url(token)

        # 3.根据解密的数据(user_id), 查询用户信息
        if user is None:
            return http.HttpResponseBadRequest('没有此用户')
        user.eamil_active = True
        user.save()

        # 5.跳转到个人中心
        return redirect(reverse('users:center'))


# 用户中心收货地址管理(新增地址)思路
"""
一.需求(前端需要收集什么,后端需要做什么)
    前端 收集收货地址信息,然后发送ajax请求
    后端 接收数据(添加地址信息),保存数据,返回响应
二.把大体思路写下来(后端的大体思路)
    1.接收数据
    2.验证数据
    3.数据入库
    4.返回响应
三.把详细思路完善一下(纯后端)
    1.接收数据(收件人,地址,省,市,区.....)
    2.验证数据(验证邮箱,固定电话,手机号....)
    3.数据入库
    4,返回响应(返回json数据)
四.确定请求方式和路由
    post     addresses/
"""

# 用户中心收货地址管理(新增地址)思路
"""
详细思路:
    1.根据请求的条件查询/展示信息
    2.需要我们将对象列表转换为字典列表
    3.返回响应
"""


# 用户中心收货地址管理
class AddressView(View):

    def get(self, request):

        # 1.根据请求的条件查询 / 展示信息
        # todo 这里注意在过滤时加上 is_deleted,因为逻辑删除的记录不应该筛选出来
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        # 2.需要我们将对象列表转换为字典列表
        address_list = []
        for address in addresses:
            address_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "province_id":address.province_id,
                "city": address.city.name,
                "city_id":address.city_id,
                "district": address.district.name,
                "district_id":address.district_id,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email,
            })

        # 3.返回响应
        context = {
            'addresses': address_list,
            'default_address_id': request.user.default_address_id
        }
        return render(request, 'user_center_site.html', context)

    # 接收用户提交的新增收货地址信息,用点击新增按钮,触发save_addresss函数,发送的是ajax请求
    # 这里可以设置ajax请求的请求方式为post,配合前端js文件.
    def post(self, request):

        # 0.判断请求用户已有的地址数量
        # 一个人最多添加20个地址
        # 最开始先判断当前请求的用户的地址是否多余20个,如果大于等于20,直接返回响应
        # todo 获取当前用户的地址的数量
        # ①直接获取: count = Address.objects.filter(user=request.user).count()
        # ②通过关联模型的方式获取:
        count = request.user.addresses.all().count()
        if count >= 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '用户地址数量超限'})

        # 1.接收数据 --- 收件人,地址,省,市,区.....
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.检验数据 --- 验证邮箱,固定电话,手机号等
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseBadRequest('参数email有误')

        # 3.数据入库
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)

        # todo 如果当前请求的用户没有默认地址,就给它设置一个默认地址
        if not request.user.default_address:
            request.user.default_address = address
            request.user.save()

        # 4.返回响应 --- 返回json数据
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email

        }
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'address': address_dict})


# 用户中心收货地址管理(修改地址)思路
"""
一.需求(前端需要收集什么,后端需要做什么)
    前端 告诉后端,在编辑(修改)哪一条地址,即把正在编辑的地址的id传递给后端
    后端 接收前端请求,更新指定的数据
二.把大体思路写下来(后端的大体思路)
    1.接收前端提交的修改数据
    2.验证数据
    3.获取修改哪条数据(地址的id)
    4.根据id查询数据
    5.更新(修改)数据
    6.返回响应
三.把详细思路完善一下(纯后端)
    1.接收前端提交的修改数据
    2.验证数据
    3.获取修改哪条数据(地址的id)
    4.根据id查询数据
    5.更新(修改)数据
    6.返回响应
四.确定请求方式和路由
    put     addresses/id/
"""

# 用户中心收货地址管理(删除地址)思路
"""
一.需求(前端需要收集什么,后端需要做什么)
    前端 告诉后端,要删除哪一条地址,即要删除地址的id传递给后端
    后端 接收前端请求,删除指定的数据
二.把大体思路写下来(后端的大体思路)
    1.获取删除哪条数据(地址id)
    2.查询数据库
    3.删除对应id的地址信息
    4.返回响应
三.把详细思路完善一下(纯后端)
    1.获取删除哪条数据(地址id)
    2.查询数据库
    3.删除对应id的地址信息
    4.返回响应
四.确定请求方式和路由
    delete     addresses/id/
"""


# 用户中心收货地址管理(修改地址)
class AddressUpdateView(View):

    # 修改地址
    def put(self, request, address_id):

        # 1.接收前端提交的修改数据
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2.验证数据
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseBadRequest('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseBadRequest('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseBadRequest('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseBadRequest('参数email有误')

        # 3.获取修改哪条数据(id)
        # 4.根据id查询数据
        # address = Address.objects.get(id=address_id)
        # 5.更新(修改)数据
        # address.receiver=receiver
        # address.mobile=mobile
        # address.save()

        # 3.获取修改哪条数据(地址的id)
        # 4.根据id查询数据
        # 5.更新(修改)数据
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})

        # 6.返回响应
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'address': address_dict})

    # 删除收货地址
    def delete(self, request, address_id):

        # 1.获取删除哪条数据(地址id)
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '暂无此数据'})

        # 2.查询数据库
        # 3.删除对应id的地址信息
        # 物理删除不推荐
        # address.delete()

        # 2.查询数据库
        # 3.删除对应id的地址信息
        try:
            address.is_deleted = True
            address.save()
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '暂无此数据'})

        # 4.返回响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


"""
用户浏览记录的需求:
一.因为浏览记录是在用户中心页面展示的,我们只记录登录用户的浏览记录
二.当用户浏览某一个具体的商品的时候,我们需要将该记录添加到一个表中
    
    1.需求
        前端收集商品id和用户信息,而且是发送ajax请求
        后端是要保存数据
    2.思路
        接收数据
        验证数据
        保存数据
        返回响应
    3.详细思路(纯后端)
        1.接收数据  用户信息.商品id
        2.验证数据
        3.保存数据(后台mysql/redis中)
            在redis中以列表形式保存
            3.1 链接redis
            3.2 先删除有可能存在的这个商品的id
            3.3 再添加商品的id
            3.4 因为最近浏览里面没有分页功能,我们只能保存5条历史记录
        4.返回响应
    4. 确定请求方式和路由
        POST  
三.获取用户浏览记录的时候需要有一个展示顺序
    根据用户id,获取redis中的指定数据
    [1, 2, 3, 4]根据商品id,查询商品详细信息
    [SKU, SKU, SKU]对象转换为字典
    返回响应
        
"""


"""
1，接收数据
2.查询数据， address对象是否存在
3.如果存在，更新用户信息里面的默认地址
4.不存在的话，返回错误响应
4.存在的话返回正确响应
"""


# 设置默认收货地址
class SetDefaultAddressView(LoginRequiredJSONMixin, View):

    def put(self, request, address_id):

        user = request.user
        try:
            address = Address.objects.get(pk=address_id)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'codel': RETCODE.NODATAERR, 'errmsg': '地址不存在'})
        try:
            User.objects.filter(pk=user.id).update(default_address=address)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'codel': RETCODE.NODATAERR, 'errmsg': '用户不存在'})
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


class UserBrowseHistoryView(LoginRequiredJSONMixin, View):

    def get(self, request):

        # 1.获取用户id
        user_id = request.user.id

        # 2.链接redis数据库
        redis_conn = get_redis_connection('history')

        # 3.根据用户id在数据库中获取响应的商品id
        ids = redis_conn.lrange('history_%s' % user_id, 0, 4)

        # 4.根据商品id获取商品对象
        # 5.将商品信息的对象列表转换为字典列表
        sku_list = []
        for id in ids:
            sku = SKU.objects.get(id=id)
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })

        # 6.返回响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': sku_list})

    def post(self, request):
        """保存用户浏览记录"""

        # 1.接收数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 2.校验数据(判断是否有此sku_id对应的商品)
        try:
            # 这里也可以写成pk,primary key 主键
            # SKU.objects.get(pk=sku_id)
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '商品不存在'})

        # 3.存储数据
        # 3.1链接redis数据库
        redis_conn = get_redis_connection('history')
        # 3.2使用管道一次操作
        pl = redis_conn.pipeline()

        user_id = request.user.id

        # 先去重,删除历史记录里面同样的记录
        # count=0,移除表中所有值与value相等的值
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 再存储,从列表前面进行添加
        pl.lpush('history_%s' % user_id, sku_id)
        # 最后截取,截取history库里面的5条记录
        # 对一个列表进行修剪,也就是让列表只保留指定区间内的元素,不在指定区间内的元素都会被删除
        # todo 例如:执行ltrim list 0 2 ,表示只保留列表list的前三个元素,其余元素全部删除
        pl.ltrim('history_%s' % user_id, 0, 4)
        # 执行管道
        pl.execute()

        # 4.返回响应

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


"""找回密码"""


# 找回密码(第0步, 点击忘记密码后进行跳转)
#   请求方式和路由
#       find_password/
#           GET     find_password/
class FindPwdView(View):

    def get(self, request):

        return render(request, 'find_password.html')


# 找回密码(第四步, 修改密码)
#   请求方式和路由
#       users/'+ this.user_id +'/password/
#           POST    users/(?P<user_id>\d+)/password/
class ChangePwdView(View):

    def post(self, request, user_id):

        # 1.接收数据
        user = User.objects.get(pk=user_id)
        json_dict = json.loads(request.body.decode())
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        access_token = json_dict.get('access_token')

        # 2.验证数据
        if not all([password, password2]):
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'message': '参数不齐'})

        # 3.判断密码是否一致
        if not re.match(r'[0-9a-zA-Z_]{8,20}', password):
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'message': '密码不合法'})
        if password2 != password:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'message': '两次输入密码不一致'})

        # 4.保存新密码
        user.password = password
        user.save()

        # 5.返回响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})




