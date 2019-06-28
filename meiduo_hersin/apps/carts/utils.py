"""
因为普通用户登录,或QQ,微信,微博用户登录都会用到这个合并的方式
因此我们把合并的这个方法进行一个封装
"""
import base64
import pickle

from django_redis import get_redis_connection

"""
思路一: 普通账号/qq/微信/微博用户登录时都可以进行合并
思路二: 合并方式可以选择将cookie里面数据合并到redis中

步骤:
1.获取cookie里面的数据   
    carts: {sku_id1:{count:xxx, selected:xxx}, 
            sku_id2:{count:xxx, selected:xxx},
            ......
            }
2.读取redis里面的数据
    hash  user_id:        sku_id1:count
                          sku_id2:count
                          ......
    set   selected_ids:   {sku_id1, sku_id2.......}
3.合并之后形成新的数据
    对cookie里面的数据进行遍历
    合并的原则: ① cookie里面有的,redis里没有的,将cookie数据加进去
               ② cookie里面有的,redis也有,数据更新为cookie里面数据
               ③ 选中状态以cookie里面的为主
    
4.把合并之后的数据更新到redis里面去
    
5.删除cookie里面的数据
"""


def merge_cookie_to_redis(request, user, response):

    # 1.获取cookie里面的数据
    cookie_str = request.COOKIES.get('carts')
    if cookie_str is None:
        pass
    else:
        carts = pickle.loads(base64.b64decode(cookie_str))

    # 2.初始化数据
    # todo 这里思路转变,将cookie里面的数据转换为redis里面的类型,后面直接对redis里面的数据进行更新
    # 2.1 hash里面的数据最终要更新到redis里面去 {sku_id1:count1, sku_id2:count2}
    cookie_hash = {}
    # 2.2 勾选数据分组和未勾选数据
    # todo 思路:cookie里面勾选的全部加到redis里面去,从redis里面删掉cookie里面没打钩的
    selected_ids = []
    unselected_ids = []

    # 3.合并之后形成新的数据
    # 对cookie里面的数据进行遍历,并分别放到上面初始化后的数据里面去
    #     合并的原则: ① cookie里面有的,redis里没有的,将cookie数据加进去
    #                ② cookie里面有的,redis也有,数据更新为cookie里面数据
    #                ③ 选中状态以cookie里面的为主
    for sku_id, count_selected_dict in carts.items():
        # todo 哈希表类似一个大的字典, 给哈希表里面添加数据,使用for循环添加多个键值对
        cookie_hash[sku_id] = count_selected_dict['count']
        # 这里进行判断,如果商品的selected属性true,放到selected_id里面去
        if count_selected_dict['selected']:
            selected_ids.append(sku_id)
        else:
            unselected_ids.append(sku_id)
    # 4.把合并之后的数据更新到redis里面去
    # 4.1 链接redis
    redis_conn = get_redis_connection('carts')
    # 4.2合并hash  合并多个键值对使用hmset  redis_conn.hmset('carts_%s'%user.id,cookie_hash)
    redis_conn.hset('carts_%s' % user.id, cookie_hash)
    # 3. 合并集合set
    if len(selected_ids) > 0:
        redis_conn.sadd('selected_%s' % user.id, *selected_ids)
    if len(unselected_ids) > 0:
        redis_conn.srem('selected_%s' % user.id, *unselected_ids)

    # 5.删除cookie里面的数据
    response.delete_cookie('carts')

    return response

