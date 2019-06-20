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


class AreasView(View):
    def get(self, request):
        parent_id = request.GET.get('area_id')
        if parent_id is None:
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
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'province_list': province_list})

        else:
            sub_areas = Area.objects.filter(parent_id=parent_id)
            aub_list = []
            for sub in sub_areas:
                aub_list.append({
                    'id': sub.id,
                    'name': sub.name
                })
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'sub_data': aub_list})
            pass  # 查询市区县的信息
