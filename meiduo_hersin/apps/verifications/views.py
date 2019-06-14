import random

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

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
        if not [mobile, image_code, uuid]:
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

        # 5.先把短信验证码保存起来
        #     redis保存, key: value方式
        redis_conn.setex('sms_%s' % mobile, sms_code_expire_time, sms_code)
        # 这里设置一个send_flag,用来判断是否已经给用户发过短信
        redis_conn.setex('send_flag%s' % mobile, 60, 1)

        # 6.最后发送短信
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        return http.JsonResponse({'code': RETCODE.OK, 'msg': '短信验证码发送成功!'})



