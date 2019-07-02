from django.conf.urls import url
from . import views

urlpatterns = [
    # url(r'^$', views.  )
    # 这里可以给匹配的路由起个名字,见名知意
    url(r'^register/', views.RegisterView.as_view(), name='register'),
    url(r'^usernames/(?P<username>[0-9a-zA-Z_]{5,20})/count/$', views.UsernameCountView.as_view(), name='usernamecount'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^center/$', views.UserCenterInfoView.as_view(), name='center'),
    url(r'^emails/$', views.EmailView.as_view(), name='email'),
    url(r'^email_active/$', views.EmailActiveView.as_view(), name='emailactive'),
    url(r'^addresses/$', views.AddressView.as_view(), name='addresses'),
    url(r'^addresses/(?P<address_id>\d+)/$', views.AddressUpdateView.as_view(), name='updateaddress'),
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.SetDefaultAddressView.as_view(), name='defaultaddress'),
    url(r'^browse_histories/$', views.UserBrowseHistoryView.as_view(), name='addhistory'),

    # todo --------------------------------------------------------------------------------------------
    # url('^password/$', views.PwdView.as_view()),
    # 获取找回密码页面
    url('^find_password/$', views.FindPwdView.as_view()),
    # 找回密码第三步，修改密码
    url('^users/(?P<user_id>\d+)/password/$', views.ChangePwdView.as_view()),
]