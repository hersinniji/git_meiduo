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

]