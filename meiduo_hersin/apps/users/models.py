from django.db import models

# Create your models here.

"""
1. 自己定义模型
    class User(models.Model):
        username = 
        password = 
        mobile = 
    密码是明文,我们自己要完成验证,等等问题
2. 我们发现我们在学习基础的时候,django自带了admin后台管理
    admin 后台管理,也有用户信息的保存和认证,密码是密文,也可以验证用户信息
    所以本次使用django自带的用户模型
"""
# 当系统的类/方法不能满足我们需求的时候,我们就继承/重写
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    moble = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
