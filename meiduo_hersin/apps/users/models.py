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


# 用户模型的定义
class User(AbstractUser):

    moble = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False, verbose_name='邮箱激活状态')
    # 由于一个用户只有一个默认地址,因此这里可以直接将默认地址字段定义在用户信息里面,
    # 外键指向用户地址模型,这样可以直接关联到用户的默认收货地址完整信息
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


# todo 因为收货地址是跟用户相关的,所以将收货地址的模型应该放在user子应用下面
from utils.models import BaseModel


class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']