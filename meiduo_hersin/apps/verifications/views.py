from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.verifications.constants import image_code_expire_time
from libs.captcha.captcha import captcha

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
