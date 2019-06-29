from decimal import Decimal

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from apps.users.models import Address

import logging
logger = logging.getLogger('django')


# 结算订单
"""
一 需求
    前端: 把用户信息给后端,后端可以根据用户id从redis里面查询到用户的购物车信息
    后端: 需要返回响应信息(包含 订单信息/地址信息)
二 大体思路
    获取登录用户的地址信息
    获取登录用户选中的商品信息
三 详细思路
    1.获取用户信息
    2.获取登录用户的地址信息
    3.获取登录用户选中的商品信息redis
        3.1 链接redis
        3.2 hash
        3.3 set
        3.4 对数据进行一下转换,同时我们需要重新组织数据
            这个数据只包含选中的商品和数量
        3.5 根据id查询商品的详细信息
        3.6 统计 总金额和总数量 运费信息
四 确定请求方式和路由
    GET   order/place/
"""


# 结算订单是从Redis购物车中查询出被勾选的商品信息进行结算并展示。
class PlaceOrderView(LoginRequiredMixin, View):

    def get(self, request):

        # 1.获取用户信息(必须是登录用户才能进入订单结算界面)
        user = request.user

        # 2.查询地址信息(地址为空则跳转到地址编辑页面)
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Exception as e:
            logger.error(e)
            return render(request, 'place_order.html', context={'errmsg': '地址查询失败'})

        # 3.从redis购物车中查询出被勾选的商品的信息
        redis_conn = get_redis_connection('carts')
        # 3.1 连接hash
        redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        # 3.2 连接set
        cart_seleced = redis_conn.smembers('selected_%s' % user.id)
        # 3.3对数据进行一下转换,同时我们需要重新组织数据
        #     这个数据只包含选中的商品id和数量
        carts = {}
        for sku_id in cart_seleced:
            carts[int(sku_id)] = int(redis_cart[sku_id])

        # 4.要返回的值(商品对象列表skus,单个商品总价和数量,总价和总数量,运费)
        # todo 4.1获取所有被勾选的商品对象
        skus = SKU.objects.filter(id__in=carts.keys())
        # todo 注意:在计算的总值跟多个对象/每个对象都有关系时,第一想到遍历
        # 4.2 初始化总价和总个数
        total_count = 0
        total_amount = Decimal(0.00)  # todo 注意: 价格使用Decimal
        for sku in skus:
            # todo 动态绑定属性 (直接作用于每一个商品!!!)
            # 单种商品个数
            sku.count = carts[sku.id]
            # 单种商品总价
            sku.amount = sku.count * sku.price

            total_amount += sku.amount
            total_count += sku.count

        # 补充运费
        freight = Decimal('10.00')

        # 5.渲染界面(准备要返回的数据)
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight

        }

        # 6.返回响应
        return render(request, 'place_order.html', context)
