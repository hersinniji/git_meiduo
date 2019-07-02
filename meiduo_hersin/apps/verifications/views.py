import json
import random
import re

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.users.models import User
from apps.users.utils import get_user_by_username
from apps.verifications.constants import image_code_expire_time, sms_code_expire_time
from libs.captcha.captcha import captcha
from libs.yuntongxun.sms import CCP

from utils.response_code import RETCODE

import logging
logger = logging.getLogger('django')

"""
一.把需求写下来(前端需要收集什么 后端需要收集什么)
    前端需要生成一个随机码(uuid),把这个随机码给后端
    
    后端需要生成图片验证码,把这个图片验证码的内容保存到redis中 
    redis的数据是 uuid:xxxx 有有效期

二.把大体思路写下来(后端的大体思路)
    1.生成图片验证码和获取图片验证码的内容
    2.连接redis,将图片验证码保存起来 uuid:xxxx 有有效期
    3.返回图片验证码
    
三.把详细思路完善一下(纯后端)
    1.生成图片验证码和获取图片验证码的内容
    2.连接redis
    3.将图片验证码保存起来,uuid:xxx 有有效期
    4.返回图片验证码
    
四.确定请求方式和路由
    图片验证码是image标签,image标签默认是通过get方式获取内容
    GET image_codes/(?P<uuid>[\w-]+)/
    GET image_codes/?uuid=xxxx
"""


class ImageCodeView(View):
    def get(self, request, uuid):
        # 1.生成图片验证码
        text, image = captcha.generate_captcha()
        # 2.连接reis
        redis_conn = get_redis_connection('code')
        # 3.将图片验证码保存起来
        # 这里记得增加过期时间,为了增加代码的可读性
        # 将这个时间定义为一个常量,这里直接调用,见名知意
        redis_conn.setex('img_%s' % uuid, image_code_expire_time, text)
        # 4.返回图片验证码
        return http.HttpResponse(image, content_type='image/jpeg')


# 短信验证
"""
开发流程:
(总体思路:用户点击获取短信验证码按钮,我们就给用户发送短信)

一.需求(前端需要做什么,后端需要做什么)
    前端需要收集:手机号,用户输入的图片验证码内容和uuid
    通过ajax发送给后端
二.大体思路(后端的大体思路)
    接收参数
    验证参数
    发送短信
三.详细思路(纯后端)
    1.接收参数(手机号,用户输入的图片验证码,uuid)
    2.验证参数
        验证手机号
        三个参数必须有不能为空
    3.验证用户输入的图片验证码和服务器保存的图片验证码一致
        3.1用户的图片验证码
        3.2服务器的验证码
        3.3比对
    4.先生成一个随机短信码
    5.先把短信验证码保存起来
        redis保存,key:value方式
    6.最后发送
四.确定请求方式和路由
    GET
    采用混合的方式
     /sms_codes/(?P<mobile>1[3-9]\d{9})/?uuid=xxx&iamgecode=xxx
    ①取URL的特定部分，如/weather/beijing/2018，可以在服务器端的路由中用正则表达式截取；
    ②查询字符串（query string)，形如key1=value1&key2=value2；
   
"""


class SmsCodeView(View):

    def get(self, request, mobile):

        # 1.接收参数(手机号, 用户输入的图片验证码, uuid)
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.验证参数
        #     验证手机号
        #     三个参数必须有不能为空
        if not all([mobile, image_code, uuid]):
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必须的参数'})

        # 操作外界资源(redis, mysql, file)时,进行异常捕获和处理
        try:
            # 3.验证用户输入的图片验证码和服务器保存的图片验证码一致
            redis_conn = get_redis_connection('code')
            redis_code = redis_conn.get('img_%s' % uuid)

            #     3.1用户的图片验证码
            #     3.2服务器的验证码
            #     3.3比对
            if redis_code is None:
                return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码过期'})

            # 添加一个删除图片验证码的逻辑
            # 1. 删除可以防止用户再次比对
            # 2. 因为redis数据库是保存在内存中,因此,不用的话就删掉,节省内存空间
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '数据库错误!'})

        # 我们获取的redis数据都是bytes类型
        if redis_code.decode().lower() != image_code.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码错误'})

        # 如果发过那么稍等再发,用来提示用户发送太过频繁
        sms_send_flag = redis_conn.get('send_flag%s' % mobile)
        if sms_send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '短信发送太过频繁!'})

        # 4.先生成一个随机短信码
        sms_code = '%06d' % random.randint(0, 999999)

        # # 5.先把短信验证码保存起来
        # #     redis保存, key: value方式
        # redis_conn.setex('sms_%s' % mobile, sms_code_expire_time, sms_code)
        # # 这里设置一个send_flag,用来判断是否已经给用户发过短信
        # redis_conn.setex('send_flag%s' % mobile, 60, 1)

        # 这里注意:
        # 给redis服务器里面存数据时为两次.如果Redis服务端需要同时处理多个请求,
        # 加上网络延迟,那么服务端利用率不高,效率较低,这时可以考虑使用管道来统一发送.
        # 管道是基础Redis类的子类,它为在单个请求中向服务器缓存多个命令提供支持,
        # 它们可以用于通过减少客户端和服务器之间来回TCP数据包的数量来显著提高命令组的性能


        # 5.先把短信验证码保存起来(使用pipeline管道)
        # ①创建管道
        pipe = redis_conn.pipeline()
        # ②
        pipe.setex('sms_%s' % mobile, sms_code_expire_time, sms_code)
        pipe.setex('send_flag%s' % mobile, 60, 1)
        # ③让管道运行
        pipe.execute()

        # 6.最后发送短信
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)

        from celery_tasks.sms.tasks import send_sms_code
        # send_sms_code 的参数平移到 delay 中
        send_sms_code.delay(mobile, sms_code)

        return http.JsonResponse({'code': RETCODE.OK, 'msg': '短信验证码发送成功!'})


# 找回密码(第一步,获取发送短信的token)
#   请求方式和路由:
#       accounts/' + this.username + '/sms/token/?text='+ this.image_code + '&image_code_id=' + this.image_code_id
#           GET     accounts/(?P<username>\w+)/sms/token/
class PwdCodeView(View):

    def get(self, request, username):

        # 1.后端需要接收数据(username,用户输入的图片验证码, uuid)
        image_code = request.GET.get('text')
        uuid = request.GET.get('image_code_id')

        # 2.验证请求参数是否为空
        if not [username, image_code, uuid]:
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必须的参数'})

        # 3.判断用户是否符合规则
        if not re.match(r'^[0-9a-zA-Z_]{5,20}$', username):
            return http.HttpResponseBadRequest('用户名不符合规则')

        # 4.验证用户输入的图片验证码和服务器保存的图片验证码一致
        # 4.1 从redis里面获取验证码
        try:
            redis_conn = get_redis_connection('code')
            redis_code = redis_conn.get('img_%s' % uuid)
            # 4.1.1用户的图片验证码
            # 4.1.2服务器的验证码
            # 4.1.3判断验证码是否已经过期
            if redis_code is None:
                return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码已过期'})
            # 4.1.4添加一个删除图片验证码的逻辑
            #   ① 删除可以防止用户再次比对
            #   ② 因为redis数据库是保存在内存中,因此,不用的话就删掉,节省内存空间
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '操作redis数据库出现错误!'})
        # 4.2 比对 (redis数据都是bytes类型)
        if redis_code.decode().lower() != image_code.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码错误'})

        # 5.从数据库中查询对应的用户名对应的手机号
        # 根据传入的username获取user对象。username可以是手机号也可以是账号
        user = get_user_by_username(username)
        mobile = user.moble

        # 6.todo 组织数据
        json_str = json.dumps({"user_id": user.id, 'mobile': user.moble})

        # 7.返回响应
        return http.JsonResponse({'mobile': mobile, 'access_token': json_str})


# 找回密码(第二步, 发送短信)''
#   请求方式和路由:
#       sms_codes/?access_token='+ this.access_token
#           GET     sms_codes/
class PwdSMSCodeView(View):

    def get(self, request):

        # 1.接收请求数据
        access_token = request.GET.get('access_token')
        user_dict = json.loads(access_token)
        mobile = user_dict.get('mobile')

        # 2.链接redis数据库mo
        redis_conn = get_redis_connection('code')

        # 3.判断用户是否已经给用户发过短信, 如果发过那么稍等再发, 用来提示用户发送太过频繁
        sms_send_flag = redis_conn.get('send_flag%s' % mobile)
        if sms_send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'message': '短信发送太过频繁!'})

        # 4.先生成一个随机短信码
        sms_code = '%06d' % random.randint(0, 999999)

        # 5.短信验证码保存起来(使用pipeline管道)
        # ①创建管道
        pipe = redis_conn.pipeline()
        # ②操作数据
        pipe.setex('sms_%s' % mobile, sms_code_expire_time, sms_code)
        pipe.setex('send_flag%s' % mobile, 60, 1)
        # ③让管道运行
        pipe.execute()

        # 6.发送短信
        from celery_tasks.sms.tasks import send_sms_code
        # send_sms_code 的参数平移到 delay 中
        send_sms_code.delay(mobile, sms_code)

        # 7.返回响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


# 找回密码(第三步, 表单提交，验证手机号，获取修改密码的access_token)
#   请求方式和路由
#       accounts/' + this.username + '/password/token/?sms_code=' + this.sms_code
#           GET     accounts/(?P<username>\w+)/password/token/
class PwdCheckCodeView(View):

    def get(self, request, username):

        # 1.接收请求参数
        user = User.objects.get(username=username)
        sms_code = request.GET.get('sms_code')

        # 2.校验短信验证码是否为空
        if sms_code is None:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'message': '短信验证码为空'})

        # 3.连接redis,判断短信验证码是否一致
        redis_conn = get_redis_connection('code')
        sms_code_server = redis_conn.get('sms_%s' % user.moble)
        if sms_code != sms_code_server.decode():
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'message': '输入的短信验证码有误'})

        # 4.组织数据
        json_str = json.dumps({"user_id": user.id, 'mobile': user.moble})

        # 5.返回响应
        return http.JsonResponse({'user_id': user.id, 'access_token': json_str})




