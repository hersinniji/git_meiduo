"""
定义QQ登录模型类
"""

from django.db import models


# 定义模型类基类,用于增加数据新建时间和更新时间
class BaseModel(models.Model):
    """为模型类补充字段"""

    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True  # 说明是抽象类,用于继承使用,数据库迁移时不会创建BaseModel的表
