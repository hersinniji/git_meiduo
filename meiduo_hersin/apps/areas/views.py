from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.areas.models import Area
from utils.response_code import RETCODE

"""
查询省的数据
    select * from tb_areas where parent_id=NULL
查询市/区县的数据
    select * from tb_areas where parent_id=XXX
    
路由:
areas/?parent_id=xxx 
areas/  获取省的信息
areas/?parent_id=xxx  获取市/区县的信息
"""

# class ProvinceView(View):
#     def get(self, request):
#         pass
#
# class ShiQuXianView(View):
#     def get(self, request, parent_id):
#         pass


# todo 数据缓存优化
"""
当我们的数据在一定时间内不经常发生变化/数据经常被查询到
我们可以将这些数据放到缓存中,以减少mysql数据库的查询

举例:
    1W用户在1秒内产生了查询
    使用缓存优化后
    1W里面有9999个使用了缓存,只有1个查询了数据库,相当于数据库的压力降低了1w倍

换句话说:
省市区的数据是我们动态查询的结果
但是省市区数据不是频繁变化的数据,所以没必要每次都重新查询
说以我们可以选择对省市区数据进行缓存处理

这时可以使用redis进行存储,也可以使用django自带的cache缓存进行存储
这里相当于把查询结果集放在了缓存(内存)中
模型---查询---查询结果集QuerySet两大特性:①惰性,②缓存

流程:
                                 ①---有缓存数据--使用缓存数据
客户端--(请求数据)--从缓存中读取数据--
                                 ②---没有缓存数据--在mysql中查询数据--在缓存中存储数据
"""

from django.core.cache import cache


class AreasView(View):
    def get(self, request):
        parent_id = request.GET.get('area_id')
        if parent_id is None:
            # todo 判断缓存中是否有数据
            # 如果缓存中没有的话,从数据库中查询,并保存在缓存中,并返回;
            # 如果缓存里面有的话,则直接返回缓存中的数据
            province_list = cache.get('pro')
            if province_list is None:

                # 这里province有很多,过滤出来后是一个一个的对象 [Area,Area,Area...]
                province = Area.objects.filter(parent_id=None)
                # 因为前端页面是使用vue去渲染数据,并且我们是使用ajax来返回响应
                # 所以这里需要将对象列表转换为字典列表,并返回回去
                province_list = []
                for item in province:
                    province_list.append({
                        'id': item.id,
                        'name': item.name
                    })

                # 把转换的数据保存到缓存(内存)中
                # cache.set(key, value, expire)
                cache.set('pro', province_list, 24*3600)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'province_list': province_list})

        else:
            # 查询 市/区县信息
            sub_list = cache.get('sub_%s' % parent_id)
            if sub_list is None:
                sub_areas = Area.objects.filter(parent_id=parent_id)
                sub_list = []
                for sub in sub_areas:
                    sub_list.append({
                        'id': sub.id,
                        'name': sub.name
                    })
                cache.set('sub_%s' % parent_id, sub_list, 24*3600)
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'sub_data': aub_list})

