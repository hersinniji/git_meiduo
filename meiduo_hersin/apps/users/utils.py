import re

from django.contrib.auth.backends import ModelBackend

from apps.users.models import User


"""
封装/抽取的思想

    为什么要封装/抽取?
    1.降低代码的耦合度    (高内聚,低耦合)
    2.提高代码的复用性    (很多地方都用到了重复的代码)
    
    抽取/封装的步骤
    1.定义一个函数(方法),把要抽取的代码复制过来
    2.哪里有问题改哪里,没有的变量以参数的形式定义
    3.验证抽取方法
    
    什么时候进行抽取/封装
    1.某几行代码实现了一个小功能我们就可以进行抽取/封装
    2.我们的代码只要第二次重复使用就抽取/封装

"""


def get_user_by_username(username):
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
    return user


class UsernameMobileModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        # 由于查询模型数据时,采用get查询单一结果,如果不存在抛出模型DoesNotExist异常
        # 所以这里使用try进行异常捕获和处理
        # try:
        #     # 用户输入的username可能是手机号或者用户名
        #     # 所以这里对username使用正则进行区分
        #     if re.match(r'1[3-9]\d{9}', username):
        #         # usernamer 是手机号
        #         user = User.objects.get(moble=username)
        #     else:
        #         # username 是用户名
        #         user = User.objects.get(username=username)
        # except User.DoesNotExist:
        #     return None
        #
        # # 这里使用系统的校验密码的方法
        # if User.check_password(password):
        #     return user
        # else:
        #     return None

        user = get_user_by_username(username)
        if user is not None and user.check_password(password):
            return user
        else:
            return None




















