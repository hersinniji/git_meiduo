"""
封装/抽取的思想

    为什么要封装/抽取?
    1.降低代码的耦合度    (高内聚,低耦合)
    2.提高代码的复用性    (很多地方都用到了重复的代码)

    抽取/封装的步骤
    1.定义一个函数(方法),把要抽取的代码复制过来
    2.哪里有问题改哪里,没有的变量以参数的形式定义
    3.验证抽取方法

    什么时候进行抽取/封装
    1.某几行代码实现了一个小功能我们就可以进行抽取/封装
    2.我们的代码只要第二次重复使用就抽取/封装

"""

from apps.oauth.constants import openid_token_expire_time

# 1.导入TimedJSONWebSignatureSerializer
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_hersin import settings


# openid加密,接收到openid之后进行加密并返回加密后的数据
def generate_access_token(openid):

    # 2.创建实例对象
    # secret_key   秘钥   习惯上使用settings文件中的settings,secret_key
    # expire_in      过期时间      单位是秒
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=openid_token_expire_time)

    # 3.组织要加密的数据
    data = {
        'openid': openid
    }

    # 4.加密
    access_token = s.dumps(data)
    return access_token.decode()


# openid解密
def check_access_token(openid):

    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=openid_token_expire_time)
    check_openid = s.loads(openid)
    return check_openid['openid']
