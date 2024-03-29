from django.db import models

# Create your models here.

# 我们需要将订单编号和交易流水号进行关联存储，方便用户和商家后续使用。

# 定义支付结果模型类
from django.db import models
from apps.orders.models import OrderInfo
from utils.models import BaseModel


class Payment(BaseModel):
    """支付信息"""
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE, verbose_name='订单编号')
    trade_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='交易流水号')

    class Meta:
        db_table = 'tb_payment'
        verbose_name = '支付信息'
        verbose_name_plural = verbose_name

