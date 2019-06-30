import os

from alipay import AliPay
from django import http
from django.shortcuts import render

# Create your views here.

from django.views import View

from apps.orders.models import OrderInfo
from apps.pay.models import Payment
from meiduo_hersin import settings
from utils.views import LoginRequiredJSONMixin
from utils.response_code import RETCODE


"""
为了帮助开发者调用开放接口，支付宝提供了开放平台服务端 SDK，
包含 JAVA、PHP、Python、NodeJS 和 .NET 等语言版本，封装了签名&验签、HTTP 接口请求等基础功能。
"""

"""

1. 沙箱 appid

2. 沙箱网关

3. 沙箱应用私钥   
                
4. 沙箱支付宝公钥
我们自己的私钥在pay/keys/app_private_key.pem里面，公钥在支付宝的服务器里面（从终端内复制过去的）
支付宝的私钥在自己支付宝的服务器上，支付宝的公钥在我们的pay/keys/alipay_public_key.pem里面


axirmj7487@sandbox.com


1. 我们需要去创建 2对公钥和私钥
    一对是我们的
    另外一对是支付宝的

"""

"""
思路：
    1.后端生成支付宝支付的链接
    2.让前端传递订单id给后端
    3.后端重定向页面到支付宝的付款页面
步骤：   
    0.接收验证订单
    1.创建alipay实例对象
    2.生成order_string
    3.拼接调转的url
    4.返回    
    
请求方式和路由:
   GET    payment/(?P<order_id>\d+)/
"""


# 订单支付功能实现  payment:付款
class PaymentView(LoginRequiredJSONMixin, View):
    """订单支付功能"""

    def get(self, request, order_id):

        # 1.获取用户信息
        user = request.user

        # 2.查询要支付的订单信息
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=request.user,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '订单信息不存在'})

        # 3.创建支付宝支付对象 (appid, 回调url, 私钥,公钥路径, 签名类型)
        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # 签名类型
            debug=True
        )

        # 4.生成登录支付宝的连接
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject='美多商城%s' % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )
        # 5.响应登录支付宝的连接
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        pay_url = settings.ALIPAY_URL + '?' + order_string

        # 6.返回响应(支付宝登录链接)
        return http.JsonResponse({'code': RETCODE.OK, 'pay_url': pay_url})


# 支付宝付款成功后回调的请求 (请求中携带支付宝返回给商家的信息,包括订单和交易流水单)
"""
GET   payment/status/
"""


# 保存订单支付结果并重定向到交易成功后的界面
class PaymentStatusView(View):
    """保存订单支付结果"""

    def get(self, request):

        # 1.获取前端（支付宝的get请求）传入的请求参数
        query_dict = request.GET
        data = query_dict.dict()

        # 2.获取并从请求参数中剔除签名信息 signature
        signature = data.pop('sign')

        # 3.创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 4.校验这个重定向是否是alipay重定向过来的
        # alipay的对象调用verify校验方法，参数为通过GET请求传入的参数和剔除signature后的请求参数
        success = alipay.verify(data, signature)
        # 如果是支付宝重定向过来的请求，处理后页面跳转至交易成功界面
        if success:
            # 4.1读取订单信息order_id
            order_id = data.get('out_trade_no')
            # 4.2读取交易流水单
            trade_id = data.get('trade_no')
            # 4.3将订单号和交易流水号保存至模型内
            Payment.objects.create(
                order=order_id,
                trade_id=trade_id
            )
            # 4.4修改订单状态为待评价
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
                status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT']
            )
            # 4.5响应交易流水号
            context = {
                'trade_id': trade_id
            }
            return render(request, 'pay_success.html', context)
        # 如果订单失败，重定向到我的订单
        else:
            return http.HttpResponseForbidden('非法请求')
