from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.contents.models import ContentCategory
from apps.contents.utils import get_categories
from apps.goods.models import SKU
from utils.response_code import RETCODE

"""

1.首页经常被访问到,首页的数据经常会被查询到,所以我们想到的是 将首页的数据进行redis的缓存操作
    以减少数据库的查询

2. 页面静态化

    我们让用户直接去访问静态的html,但是静态的html的数据 必须是数据库(业务逻辑)中最新的

    我们如何去实现静态化呢?

    ①我们可以先查询数据库,然后将查询的数据渲染到html中,将这个html写入到指定文件
    当用户访问的时候直接去访问就可以

    ②问题: 什么时候去重新生成静态化页面
        我们采用定时任务

"""


# 首页
class IndexView(View):

    def get(self, request):

        """
        1.分类信息
        2.楼层信息
        """

        # 1.分类信息 分类信息在其他页面也会出现,我们应该直接抽取为一个方法
        # 查询商品频道和分类
        categories = get_categories()

        # 2.楼层信息 广告内容
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # 渲染模板的上下文
        context = {
            'categories': categories,
            'contents': contents,
        }

        return render(request, 'index.html', context=context)


"""
使用文件存储方案 fastdfs 上传文件
    ① 上传文件需要先创建fdfs_client.client.Fdfs_client的对象，并指明配置文件
    ② 通过创建的客户端对象执行上传文件的方法
"""

# # 1.导入
# from fdfs_client.client import Fdfs_client
#
# # 2.创建客户端实例,加载指定配置文件
# client = Fdfs_client('utils/fdfs/client.conf')
#
# # 3.上传图片
# # filename 写图片的绝对路径,(ps:如果图片文件在程序的工作目录下,也可以写相对路径)
# client.upload_by_filename('/home/guaguas/Desktop/小渔船.jpg')


# 首页简单购物车展示
class SimpleCartsView(View):

    def get(self, request):

        user = request.user
        # 登录用户
        if user.is_authenticated:
            # 查询redis
            redis_conn = get_redis_connection('carts')
            # hash
            sku_id_count = redis_conn.hgetall('carts_%s' % user.id)
            cart_skus = []
            for sku_id in sku_id_count.keys():
                sku = SKU.objects.get(pk=sku_id)
                cart_skus.append({
                    'name': sku.name,
                    'count': sku_id_count[sku_id]
                })
        # 非登录用户
        else:
            # 获取cookie信息
            cookie_str = request.COOKIES.get('carts')
            cart_skus = []
            for sku_id, count_selected in cookie_str.items():
                sku = SKU.objects.get(pk=sku_id)
                cart_skus.append({
                    'name': sku.name,
                    'count': count_selected['count']
                })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'cart_skus': cart_skus})
