from django.db import models
from utils.models import BaseModel

# Create your models here.

# todo 定义 QQ身份(openid) 与 用户模型类User 的关联关系


class OAuthQQUser(BaseModel):
    """QQ登录用户数据"""

    # Foreignkey 使用了其他子应用的模型
    # 这里采用‘子应用名.模型类名’
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    # openid是此网站上唯一对应用户身份的标识，网站可将此ID进行存储便于用户下次登录时辨识其身份
    # 或将其与用户在网站上的原有账号进行绑定。
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        # verbose_name指定在admin管理界面中显示中文；verbose_name表示单数形式的显示
        # verbose_name_plural表示复数形式的显示；中文的单数和复数一般不作区别。
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name
