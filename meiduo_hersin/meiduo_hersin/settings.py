"""
Django settings for meiduo_hersin project.

Generated by 'django-admin startproject' using Django 1.11.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ode2i%*gyip-jlf5n27(o9vdsa62a_ir)n-%_l%=96h6gu%%(b'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# 这是一个安全机制,允许我们以什么形式(域名/Ip)来访问后端
# 默认是 127.0.0.1
ALLOWED_HOSTS = ['www.meiduo.site', '127.0.0.1']


AUTH_USER_MODEL = 'users.User'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'apps.areas.apps.AreasConfig',
    'apps.oauth.apps.OauthConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.contents.apps.ContentsConfig',
    'apps.pay.apps.PayConfig',
    'apps.goods.apps.GoodsConfig',
    'apps.users.apps.UsersConfig',  # 因为我们的子应用已经放到apps的包中,所以要添加apps.xxx
    'django.contrib.staticfiles',
    'django_crontab',  # 定时任务
    'haystack',
]

# 静态文件生成定时器
CRONJOBS = [
    # 每1分钟生成一次首页静态文件

    # 参数1: 频次
    # 分 时 日 月 周

    # 参数2: 任务(函数)

    # 参数3: 日志
    ('*/1 * * * *', 'apps.contents.crons.generate_static_index_html', '>> ' + os.path.join(BASE_DIR, 'logs/crontab.log'))
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meiduo_hersin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'utils.jinja2_environment.jinja2_environment',
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'meiduo_hersin.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # 数据库引擎
        'HOST': '127.0.0.1',  # 数据库主机
        'PORT': 3306,  # 数据库端口
        'USER': 'root',  # 数据库用户名
        'PASSWORD': 'suboyang',  # 数据库用户密码
        'NAME': 'meiduo_hersin'  # 数据库名字
    },
}


# 这里使用 redis数据库 的目的是为了在内存中存储session数据
CACHES = {
    "default": {  # 默认
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "session": {  # session
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "code": {  # code
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "history": {  # 用户浏览记录是临时数据，且经常变化，数据量不大，所以我们选择内存型数据库进行存储。
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://127.0.0.1:6379/3",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        },
    "carts": {  # 用户浏览记录是临时数据，且经常变化，数据量不大，所以我们选择内存型数据库进行存储。
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": "redis://127.0.0.1:6379/4",
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                }
        },

}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

# 告知系统去哪里找静态文件
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方法
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/meiduo.log'),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}

# 修改默认的用户认证后端
AUTHENTICATION_BACKENDS = [
    # 'django.contrib.auth.backends.ModelBackend'
    'apps.users.utils.UsernameMobileModelBackend',
]


# LOGIN_URL 的默认值是 : accounts/login/
# 我们只需要修改这个配置信息就可以,修改成 符合我们的路由就可以
LOGIN_URL = '/login/'


# QQ登录相关的
QQ_CLIENT_ID = '101518219'

QQ_CLIENT_SECRET = '418d84ebdc7241efb79536886ae95224'

QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'


# 发送邮件相关
# 指定邮件发送后端
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# 邮件服务器
EMAIL_HOST = 'smtp.163.com'
# smtp默认端口号是25
EMAIL_PORT = 25
# 发送邮件的邮箱
EMAIL_HOST_USER = 'qi_rui_hua@163.com'
# 在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = '123456abc'
# 收件人看到的发件人
EMAIL_FROM = '美多商城<qi_rui_hua@163.com>'


"""
首页图片数据展示时
image = models.ImageField(null=True, blank=True, verbose_name='图片')
里面的ImageField方法不满足要求
自定义完成了存储类之后,告诉系统,使用我们自己定义的存储类
"""

# 指定自定义的Django文件存储类
DEFAULT_FILE_STORAGE = 'utils.fdfs.faststorage.MyStorage'

# # FastDFS相关参数
# # FDFS_BASE_URL = 'http://172.16.62.129:8888/'
# FDFS_BASE_URL = 'http://image.meiduo.site:8888/'


# Haystack 搜索引擎相关
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://172.16.62.129:9200/',  # Elasticsearch服务器ip地址，端口号固定为9200
        'INDEX_NAME': 'haystack',  # Elasticsearch建立的索引库的名称
    },
}


# 支付宝SDK配置参数
ALIPAY_APPID = '2016101100662156'
ALIPAY_DEBUG = True
ALIPAY_URL = 'https://openapi.alipaydev.com/gateway.do'
ALIPAY_RETURN_URL = 'http://www.meiduo.site:8000/payment/status/'
APP_PRIVATE_KEY_PATH = os.path.join(BASE_DIR, 'apps/pay/keys/app_private_key.pem')
ALIPAY_PUBLIC_KEY_PATH = os.path.join(BASE_DIR, 'apps/pay/keys/alipay_public_key.pem')
