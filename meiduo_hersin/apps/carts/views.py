# 思路分析
"""
一 把需求写下来 (前端需要收集什么 后端需要做什么)

二 把大体思路写下来(后端的大体思路)

三 把详细思路完善一下(纯后端)

四 确定我们请求方式和路由

"""

# Create your views here.
import base64
import json
import pickle

from django import http
from django.shortcuts import render

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


# 购物车的实现
class CartView(View):

    # 增加购物车
    def post(self, request):

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

            # 创建管道
            pl = redis_conn.pipeline()

            # 4.2存储(hash, set)
            # HSET key field value
            # 将哈希表key中的域field的值设为value 。
            # pl.hset('carts_%s' % request.user.id, sku_id, count)
            # todo 这里需要注意.如果这样写的话,再次往购物车加之前加过得商品.不会累计数量,只会覆盖原有数量
            # 所以不满足要求,这里可以使用哈希类型自带的hincrby(),实现在原有基础上,进行加本次的数据操作
            pl.hincrby('carts_%s' % request.user.id, sku_id, count)
            # SADD key member[member...]
            # 将一个或多个member元素加入到集合key当中，已经存在于集合的member元素将被忽略。
            pl.sadd('selected_%s' % request.user.id, sku_id)

            # 执行管道
            pl.execute()

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

    # 查询购物车
    def get(self, request):

        """
        一 把需求写下来 (前端需要收集什么 后端需要做什么)


        二 把大体思路写下来(后端的大体思路)
            1.获取用户信息,根据用户信息进行判断
            2.登陆用户redis查询
                2.1 连接redis
                2.2 hash   {sku_id:count}
                2.3 set     [sku_id]

            3.未登录用户cookie查询
                3.1 读取cookie
                3.2 判断carts数据,如果有则解码数据,如果没有则初始化一个字典
                    {sku_id: {count:xxx,selected:xxxx}}

            4.根据id查询商品信息信息
            5.展示
        三 把详细思路完善一下(纯后端)
            1.获取用户信息,根据用户信息进行判断用户是否登录
            2.登录用户redis查询
                链接redis
                hash  {sku_id:count}
                set   被勾选商品的id [sku_id]
            3.未登录用户cookie查询
                获取/读取cookie信息
                判断carts数据   carts:{sku_id:{count:xxx, selected:xxx}}
                如果有则解码数据
                没有则初始化一个空字典
            4.根据id查询商品信息
            5.返回响应
        四 确定我们请求方式和路由
            GET   carts/
        """

        # 1.获取用户信息, 根据用户信息进行判断用户是否登录
        user = request.user

        # 2.登录用户redis查询
        if user.is_authenticated:
            # 链接redis
            redis_conn = get_redis_connection('carts')
            # hash哈希类型  user_id  {sku_id:count}
            sku_id_count = redis_conn.hgetall('carts_%s' % user.id)
            # set无序集合   被勾选商品的id [sku_id]
            selected_ids = redis_conn.smembers('selected_%s' % user.id)

            # 为了后面统一获取sku_id时都是从一个数据类型中获取的,这里将登录后信息也转为一个字典
            # 将redis的数据统一为cookie的格式 或者
            # 将cookie的数据统一为redis的格式
            carts = {}
            # todo 解包 dict.items()
            for sku_id, count in sku_id_count.items():
                if sku_id in selected_ids:
                    selected = True
                else:
                    selected = False
                # todo 注意redis的数据类型都是bytes类型,因此这里需要进行转换,转为int类型
                carts[int(sku_id)] = {
                    'selected': selected,
                    'count': int(count)
                }

        # 3.未登录用户cookie查询
        else:
            # 获取/读取cookie信息
            cookie_str = request.COOKIES.get('carts')
            # 判断carts数据   carts:{sku_id:{count:xxx, selected:xxx}}
            if cookie_str is None:
                # 没有则初始化一个空字典
                carts = {}
            else:
                # 如果有则解码数据
                carts = pickle.loads(base64.b64decode(cookie_str))

        # 4.todo 根据id查询商品信息 cookie里面为:
        # carts: {
        #   sku_id1:{count:xxx, selected:xxx},
        #   sku_id2:{count:xxx, selected:xxx},
        #   }
        # 获取所有商品的id对象
        ids = carts.keys()
        # 根据商品的id获取商品的对象
        skus = SKU.objects.filter(id__in=ids)
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                # todo 注意redis的数据类型都是bytes类型,因此上面不转换的话,这里会报错
                'count': carts.get(sku.id).get('count'),
                'selected': str(carts.get(sku.id)['selected']),
                'default_image_url': sku.default_image.url,  # todo 这里注意要加上.url
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts.get(sku.id).get('count'))
            })
        context = {'cart_skus': sku_list}

        # 5.返回响应
        return render(request, 'cart.html', context)

    # 修改购物车
    def put(self, request):

        """
                一 把需求写下来 (前端需要收集什么 后端需要做什么)
                    前端 收集修改的sku_id, count, selected传递给后端, 发送ajax请求
                    后端 从数据库/cookie里面更新数据,并且返回
                二 把大体思路写下来(后端的大体思路)
                    1.接收数据
                    2.验证数据
                    3.获取用户的信息
                    4.登陆用户更新redis数据
                        4.1 连接redis
                        4.2 hash
                        4.3 set
                        4.4 返回相应
                    5.未登录更新cookie数据
                        5.1 获取cart数据,并判断
                        5.2 更新指定数据
                        5.3 对字典数据进行处理,并设置cookie
                        5.4 返回相应
                三 把详细思路完善一下(纯后端)
                    1. 接收数据(sku_id, count, selected)
                    2. 验证数据
                    3. 获取用户的信息
                    4. 登录用户更新redis数据
                        hash
                        set
                    5. 非登录用户更新cookie信息
                        carts: {sku_id1: {'count': xxx, 'selected: xxx}, sku_id2:{.........}}

                    6. 返回响应
                四 确定我们请求方式和路由
                    PUT   carts/
                """

        # 1.接收数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected')
        # 2.验证数据
        # 2.1 是否有空值
        if not all([sku_id, count]):
            return http.JsonResponse({'cdoe': RETCODE.NODATAERR, 'errmsg': '参数不齐全'})
        # 2.2 判断商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({'cdoe': RETCODE.NODATAERR, 'errmsg': '商品不存在'})
        # 2.3 判断传入的数量是否为数值
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({'cdoe': RETCODE.NODATAERR, 'errmsg': '参数错误'})
        # 3.获取用户的信息
        if request.user.is_authenticated:
            # 4.登陆用户更新redis数据
            #     4.1 连接redis
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            #     4.2 hash   user_id  sku_id: count
            pl.hset('carts_%s' % request.user.id, sku_id, count)
            pl.execute()
            #     4.3 set    selected_user_id: selected_id
            # 这里的原则就是:如果勾选,则将sku_id加进集合(集合是无重复),如果没有勾选,则从集合中原有的进行删除
            if selected:
                pl.sadd('selected_%s' % request.user.id, sku_id)
            else:
                # todo 这里原来就是未勾选怎么办?----------------------------------------------------
                pl.srem('selected_%s' % request.user.id, sku_id)
            #     4.4 返回相应
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': count * sku.price
            }
            return http.JsonResponse({'code': RETCODE, 'errmsg': 'ok', 'cart_sku': cart_sku})
        # 5.未登录更新cookie数据
        else:
            #     5.1 获取cart数据,并判断
            cart_cookie = request.COOKIES.get('carts')
            # todo ==========================================================================
            print(type(cart_cookie))
            # carts: sku_id: {'count': count, 'selected': xxx },.........
            # 判断cart_cookie是否为空,为空则初始化一个空字典, 不为空的话进行解码
            if cart_cookie is None:
                carts = {}
            else:
                carts = pickle.loads(base64.b64decode(cart_cookie))
            #     5.2 更新指定数据
            if sku_id in carts:
                carts[sku_id] = {
                    'count': count,
                    'selected': selected
                }
                # carts[sku_id]['count'] = count
                # carts[sku_id]['selected'] = selected
            en = base64.b64encode(pickle.dumps(carts))
            #     5.3 对字典数据进行处理,并设置cookie
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_sku': cart_sku})
            response.set_cookie('carts', en)
            #     5.4 返回相应
            return response

    # 删除购物车内商品
    def delete(self, request):

        """
        一 把需求写下来 (前端需要收集什么 后端需要做什么)
            前端  传要删除的sku_id
            后端  删除数据
        二 把大体思路写下来(后端的大体思路)
            1.接收数据 sku_id
            2.根据用户信息进行判断
            3.登陆用户删除redis
                3.1 连接redis
                3.2 hash
                3.3 set
                3.4 返回相应
            4.未登陆用户删除cookie
                4.1 读取cookie中的数据,并且判断
                4.2 删除数据
                4.3 字典数据处理,并设置cookie
                4.4 返回相应
        三 把详细思路完善一下(纯后端)
            1. 接收数据 sku_id
            2. 校验数据 看有没有这个商品
            3. 判断用户是否登录
            4. 登录用户
                链接redis
                hash
                set
                返回响应
            5. 未登录用户
                读取cookie中的数据,看是否有值
                删除后进行加密
                组织响应数据
                设置cookie
                返回响应
        四 确定我们请求方式和路由
            DELETE  carts/
        """

        # 1.接收数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 2.根据用户信息进行判断
        user = request.user
        if user.is_authenticated:
            # 3.登陆用户删除redis
            #     3.1 连接redis
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            #     3.2 hash
            pl.hdel('carts_%s' % request.user.id, sku_id)
            #     3.3 set
            pl.srem('elected_%s' % request.user.id, sku_id)
            pl.execute()
            #     3.4 返回相应
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
        else:
            # 4.未登陆用户删除cookie  carts { sku_id1:{'count': xxx, 'selected': xxx}, sku_id2:}
            #     4.1 读取cookie中的数据,并且判断
            cookie_data = request.COOKIES.get('carts')
            if cookie_data is None:
                carts = {}
            else:
                carts = pickle.loads(base64.b64decode(cookie_data))
            if sku_id in carts:
                # 4.2 删除字典里面的数据
                del carts[sku_id]
            en = base64.b64encode(pickle.dumps(carts))
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
            response.set_cookie('carts', en)
            # 4.3 返回响应
            return response
