import datetime
import json
from decimal import Decimal

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection
from django.utils import timezone

from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from apps.users.models import Address
from utils.response_code import RETCODE


import logging

from utils.views import LoginRequiredJSONMixin

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


# 动态添加属性示例:
# class Person(object):
#
#     name = 'itcast'
#
# p = Person()
# p.name
# # python的面向对象的一大特点: 可以动态的添加属性
# p.age=10
# p.age
#
# p2 = Person()
# p2.age


# 提交订单
"""
这里注意:用户在'订单结算界面',仅仅收集了用户选择的地址信息和付款方式,然后用户直接点击提交订单,
所以,在用户点击提交订单后,我们只需要从前端收集用户信息,地址id,付款方式即可,其他所有信息后端可自己从redis里面获取

一 需求
    前端: 收集 用户信息(随着请求cookie传递 sessionid过来的)
                地址信息,支付方式
    后端: 需要生成订单信息和订单商品信息
二 大体思路
    先订单信息,再商品信息,因为订单对商品为1对多,订单是商品的外键
三 详细思路
    1.订单信息
        1.1 获取用户信息
        1.2 获取地址信息
        1.3 获取支付方式
        1.4 生成订单id,即订单模型的主键,这里自行生成
        1.5 组织总金额 总数量 运费
        1.6 组织订单状态(待支付/付款/发货/退款...)
    2.订单内的商品信息(我们从redis中获取选中的商品信息)
        2.1 链接redis
        2.2 hash
        2.3 set
        2.4 类型转换,转换过程中重新组织数据
            组织成只有用户勾选选中的数据信息
            {sku_id1:count, sku_id2:count}
        2.5 获取选中的商品id
        2.6 遍历id
            2.7 查询
            2.8 判断库存
            2.9 库存减少,销量增加
            2.10 保存商品信息
            2.11 累加计算,总金额和总数量
    3.保存订单信息的修改
    4.删除redis中选中的商品的信息
四 请求方式和路由
    POST   order/    这里发送ajax请求
"""


class OrderView(LoginRequiredJSONMixin, View):  # 这里必须是登录用户

    def post(self, request):

        # 1.订单信息
        #     1.1 获取用户信息
        user = request.user
        json_dict = json.loads(request.body.decode())
        #     1.2 获取地址信息
        address_id = json_dict.get('address_id')
        try:
            address = Address.objects.get(pk=address_id)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '地址有误'})
        #     1.3 获取支付方式(这里增加判断,并引入字母表示支付方式,提高可读性)
        pay_method = json_dict.get('pay_method')
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        #     1.4 生成订单id
        #           order_id = 年月日时分秒 + 9位用户id
        #           Y year
        #           m month
        #           d day
        #           H hour
        #           M minute
        #           S sencode
        # todo 生成带年月日时分秒 + 用户id(自动补够9位)
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        #     1.5 组织总金额 0 总数量 0 运费

        total_count = 0
        total_amount = Decimal('0')
        freight = Decimal('10.00')
        #     1.6 组织订单状态
        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            status = OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']

        # 创建事务
        from django.db import transaction
        with transaction.atomic():
            # 一.实务的起点(回滚点)
            point_id = transaction.savepoint()

            # 增加订单记录
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=total_count,
                total_amount=total_amount,
                freight=freight,
                pay_method=pay_method,
                status=status
            )

            # 2.订单商品信息(我们从redis中获取选中的商品信息)
            #     2.1 连接redis
            redis_conn = get_redis_connection('carts')
            #     2.2 hash
            sku_id_count = redis_conn.hgetall('carts_%s' % user.id)
            #     2.3 set
            selected_ids = redis_conn.smembers('selected_%s' % user.id)
            #     2.4 类型转换,转换过程中重新组织数据
            #         选中的数据
            #         {sku_id:count,sku_id:count}
            carts = {}
            for sku_id in selected_ids:
                carts[int(sku_id)] = int(sku_id_count[sku_id])
            #     2.5 获取选中的商品id  [1,2,3]
            ids = carts.keys()
            #     2.6 遍历id
            for id in ids:
            #         2.7 查询
                sku  = SKU.objects.get(pk=id)
            #         2.8 判断库存count
                if carts[id] > sku.stock:

                    # 二.如果失败了,此处进行回滚
                    transaction.savepoint_rollback(point_id)

                    return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '库存不足'})

        #         2.9 库存减少,销量增加
        #         sku.stock -= carts[id]
        #         sku.sales += carts[id]
        #         sku.save()  # todo 注意在直接操作数据库记录对象后需要保存


                # todo 用乐观锁来实现
                # 在更新的时候判断此时的库存是否是之前查询出的库存一致
                # 一致则更新成功 返回1
                # 不一致则不更新 返回0
                # 1.记录之前的库存
                old_stock = sku.stock
                # 2.计算更新的库存
                new_stock = sku.stock - carts[id]
                new_sales = sku.sales + carts[id]
                # 3.更新的时候判断
                result = SKU.objects.filter(id=sku_id, stock=old_stock).update(stock=new_stock, sales=new_sales)
                if result == 0:
                    print('下单失败')
                    transaction.savepoint_rollback(point_id)
                    return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '下单失败'})


            #         2.10 保存商品信息
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=carts[id],
                    price=sku.price
                )
            #         2.11 累加计算 总金额和总数量
            #     total_count += carts[id]
            #     total_amount += (total_amount * sku.price)
                order.total_count += carts[id]
                order.total_amount += (total_amount * sku.price)

            # 3. 保存订单信息的修改(遍历没问题后进行订单信息的保存)
            order.save()

        # 三.所有都没问题的话,提交事物
        transaction.savepoint_commit(point_id)

        # 4. 清除redis中选中商品的信息
        # 暂缓实现   需要重复很多次

        # 5.返回响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})

