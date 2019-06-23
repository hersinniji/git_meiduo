from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View


class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')


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
