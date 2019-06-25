
# todo 自定义存储类,重写url方法

"""
1. 您的自定义存储系统必须是以下的子类 django.core.files.storage.Storage
2.Django必须能够在没有任何参数的情况下实例化您的存储系统。
    这意味着任何设置都应该来自django.conf.settings
3.您的存储类必须实现_open()和_save() 方法以及适用于您的存储类的任何其他方法
4.您的存储类必须是可解构的， 以便在迁移中的字段上使用时可以对其进行序列化。
    只要您的字段具有可自行序列化的参数，就 可以使用
    django.utils.deconstruct.deconstructible类装饰器
    （这就是Django在FileSystemStorage上使用的）

"""

from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class MyStorage(Storage):

    # def __init__(self, option=None):
    #     if not option:
    #         option = settings.CUSTOM_STORAGE_OPTIONS

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content, max_length=None):
        pass

    def url(self, name):
        # name 其实就是 file_id ,即 group1/M00/00/00/wKjlhFsTgJ2AJvG_AAAyZgOTZN0850.jpg
        # 文件索引（file_id）是客户端上传文件后Storage返回给客户端的一个字符串，是以后访问该文件的索引信息。
        # 文件索引（file_id）信息包括：组名、虚拟磁盘路径、数据两级目录、文件名等信息。
        return 'http://172.16.62.129:8888/' + name


# storage = MyStorage()


# class Person(object):
#
#     def __init__(self,name=None):
#         self.name=name
#
# p = Person(name='itcast')
#
# p = Person()
