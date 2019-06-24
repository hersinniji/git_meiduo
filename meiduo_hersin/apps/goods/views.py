from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.goods.models import SKU, GoodsCategory
from apps.goods.utils import get_breadcrumb

"""
一个页面的需求分析,先从大的方向把整体流程搞清楚
再把页面中 动态展示的数据 分析出来(需求)

再把一些需求模块化

再把需求简单化
"""

"""
一.需求(前端需要收集什么,后端需要做什么)
    前端 前端需要必须收集分类的id, 排序字段(销量.价格,人气等)和页码是可选的
    后端 后端就是根据需要查询数据
二.把大体思路写下来(后端的大体思路)
    1.根据分类id,把所有数据都查询出来
    2.如果有排序字段再进行排序
    3.如果有分页字段再分页
三.把详细思路完善一下(纯后端)
    1.根据分类id,把所有数据都查询出来
    2.如果有排序字段再进行排序
    3.如果有分页字段再分页
四.确定请求方式和路由
    get     /list/(?P<category_id>\d+)/(?P<page_num>\d+)/?sort=排序方式
"""

import logging
logger = logging.getLogger('django')


# 商品列表页
class ListView(View):

    def get(self, request, category_id, page_num):

        """
        我们需要根据当前的分类id,来获取它的上级/下级信息

        """
        # 一.面包屑实现

        try:
            # 1.获取当前的分类id,并得到分类对象
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            logger.error(e)
            return render(request, 'list.html', context={'errmsg': '没有此分类'})

        # 2.获取它的上级/下级
        # 如果是一级  一个信息
        # 如果是二级  两个信息
        # 如果是三级  三个信息
        breadcrumb = get_breadcrumb(category)

        # 二.列表数据

        # 1.如果有排序字段再进行排序
        sort = request.GET.get('sort')
        # sort = hot 人气 默认按销量进行排序
        # sort = price 价格 根据 价格排序
        # sort = default 默认 根据 create_time排序
        if sort == 'hot':
            order_filed = 'sales'
        elif sort == 'price':
            order_filed = 'price'
        else:
            order_filed = 'create_time'
            sort = 'default'

        # 2.根据分类id, 把所有数据都查询出来
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by(order_filed)

        # 3.如果有分页字段再分页
        try:
            page_num = int(page_num)
        except:
            page_num = 1

        # 3.1导入分页类
        from django.core.paginator import Paginator
        try:
            # 3.2创建分页实例对象
            paginator = Paginator(skus, 5)
            # 3.3获取分页数据
            page_skus = paginator.page(page_num)
            # 总分页
            total_page = paginator.num_pages
        except Exception as e:
            pass

        context = {
            'category': category,
            'breadcrumb': breadcrumb,
            'sort': sort,  # 排序字段
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }

        return render(request, 'list.html', context)
