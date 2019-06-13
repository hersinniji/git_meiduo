from django.conf.urls import url
from . import views

urlpatterns = [
    # url(r'^$', views.  )
    # 这里可以给匹配的路由起个名字,见名知意
    url(r'^register/', views.RegisterView.as_view(), name='register'),
    url(r'^usernames/(?P<username>[0-9a-zA-Z_]{5,20})/count/$', views.UsernameCountView.as_view(), name='usernamecount'),

]