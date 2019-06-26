import base64
import json
import pickle

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU
from utils.response_code import RETCODE

"""
购物车的实现
1.登录用户和非登录用户都可以将商品增加到购物车
2.添加商品时:
    如果是登录用户,则必须传递的是用户id,商品id,商品数量count,是否勾选selected(选中状态)
3.购物车里面信息保存在哪:
    登录用户:
        可以保存在后端(mysql/redis)
        这里使用redis,原因①:购物车信息变化频率高,经常读写;②放在mysql里面会增加mysql的压力
        放在redis里面的原则:尽量少占用内存空间
        
        分析实现:
            hash哈希类型
            user_id
                sku_id:count,
                selected_sku_id:selected
            这里使用到的key太多,占用内存空间多
        优化:
            hash:
                carts_user_id
                    sku_id:count
            set:
                carts_user_id
                    把选中的商品id保存在集合中
            这里使用集合是因为,用户id不需要有顺序
    未登录用户:
        可以放在前端,放在后端的话不方便管理控制,并且存放时间不好确定
        cookie
            sku_id, count, selected
            {
                'sku_id': {'count':xxx,'selected':true},
                'sku_id': {'count':xxx,'selected':true},
                'sku_id': {'count':xxx,'selected':true},
                'sku_id': {'count':xxx,'selected':true},  
            }
4.将cookie里面数据进行转化加密
①将数据转化为二进制数据
    pickle的速度比json快.
    pickle.dumps     将字典转换为 二进制bytes
    pickle.loads      将二进制bytes转换为字典         
    示例操作:
    import pickle
    a = {
        '1': {'count': 3, 'selected': True},
        '2': {'count': 6, 'selected': False},
        '3': {'count': 2, 'selected': True},
    }
    d = pickle.dumps(a)
    pickle.loads(d)
②将二进制数据转换为base64编码格式
    将二进制数据转换为新的编码格式
    aa = base64.b64encode(a)
    将新的编码格式转换为二进制数据
    aa = base64.b64decode(a)
    
ps:MD5也可以进行加密编码,但是其转换不可逆,同一个数据转换后结果一直一样,不安全

"""


# #############################增加数据进购物车###################################

"""
1.需求
            前端: 收集信息(商品id, 数量count, 选中状态是可选的,默认为选中)
                如果用户登录了,则请求中携带session_id
                如果用户没有登录,请求不带session_id
            后端: 增加数据到购物车
        2.大体思路
            接收数据
            验证数据
            存储数据
            返回响应
        3.详细思路
            1.接收数据(sku_id, count)
            2.验证数据
            3.根据用户是否登录来判断存储数据的位置和细节
            4.登录用户redis里面
                4.1 链接redis
                4.2 存储(hash,set)
                4.3 返回响应
            5.非登录用户 cookie里面
                5.1 转为二进制
                5.2 加密
                5.3 存在cookie里面
                5.4 返回响应
        4.请求方式和路由
            POST   carts/
"""


class CartView(View):

    def post(self, request):

        # 1.接收数据(sku_id, count)
        json_data = json.loads(request.body.decode())
        sku_id = json_data.get('sku_id')
        count = json_data.get('count')

        # 2.验证数据
        # 2.1 判断参数是否齐全
        if not all([sku_id, count]):
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '参数不齐'})
        # 2.2 判断是否存在此商品
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '商品不存在'})
        # 2.3 传过来的count数量需要是数值而不是字符串
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({'code': RETCODE.NODATAERR, 'errmsg': '商品数量参数错误'})

        # 3.根据用户是否登录来判断存储数据的位置和细节
        if request.user.is_authenticated:
            # 4.登录用户redis里面
            # 4.1链接redis
            redis_conn = get_redis_connection('carts')
            # 4.2存储(hash, set)
            # HSET key field value
            # 将哈希表key中的域field的值设为value 。
            redis_conn.hset('carts_%s' % request.user.id, sku_id, count)
            # SADD key member[member...]
            # 将一个或多个member元素加入到集合key当中，已经存在于集合的member元素将被忽略。
            redis_conn.sadd('selected_%s' % request.user.id, sku_id)
            # 4.3返回响应
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
        else:
            # 5.非登录用户cookie里面

            # # 5.1 组织数据
            # carts = {
            #     sku_id: {'count': count, 'selected': True},
            # }

            # 这里需要进行判断, 先判断cookie里面的carts是否存在
            cookie_str = request.COOKIES.get('carts')

            if cookie_str is None:
                # 如果不存在,则进行增加
                # 如果cookie数据不存在,先初始化一个 空的carts
                carts = {}
            else:
                # 如果存在.对数据进行解码,并更新count数据
                # 对数据进行base64解码
                de = base64.b64decode(cookie_str)
                # 再将bytes类型的数据转换为字典
                carts = pickle.loads(de)

            if sku_id in carts:
                origin_count = carts[sku_id]['count']
                count = count + origin_count
            carts[sku_id] = {
                'count': count,
                'selected': True
            }

            # 5.2 加密
            # 将数据转换为bytes类型
            a = pickle.dumps(carts)
            # 将bytes类型转换为base64类型
            b = base64.b64encode(a)
            # 5.3 存在cookie里面
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
            # todo 这里注意设置cookie时: set_cookie(key,string_value) 里面第二个值应为字符串
            # 而base64为bytes类型的数据,所以要对其进行解码
            response.set_cookie('carts', b.decode())

            # 5.4返回响应
            return response




