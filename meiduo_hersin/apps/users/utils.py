import re

from django.contrib.auth.backends import ModelBackend

from apps.users.models import User


class UsernameMobileModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        # 由于查询模型数据时,采用get查询单一结果,如果不存在抛出模型DoesNotExist异常
        # 所以这里使用try进行异常捕获和处理
        try:
            # 用户输入的username可能是手机号或者用户名
            # 所以这里对username使用正则进行区分
            if re.match(r'1[3-9]\d{9}', username):
                # usernamer 是手机号
                user = User.objects.get(moble=username)
            else:
                # username 是用户名
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        # 这里使用系统的校验密码的方法
        if User.check_password(password):
            return user
        else:
            return None

