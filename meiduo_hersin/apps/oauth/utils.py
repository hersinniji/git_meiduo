"""
封装抽取
"""


def openid_access_token(openid):

    # 1.导入
    from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
    from meiduo_hersin import settings

    # 2.创建实例对象
    # secret_key   秘钥   习惯上使用settings文件中的settings,secret_key
    # expire_in      过期时间      单位是秒
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)

    # 3.组织要加密的数据
    data = {
        'openid': openid
    }

    # 4.加密
    access_token = s.dumps(data)
    return access_token.decode()
