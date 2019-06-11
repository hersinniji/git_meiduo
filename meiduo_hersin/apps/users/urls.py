from django.conf.urls import url
from . import views

urlpatterns = [
    # url(r'^$', views.  )
    # 这里可以给匹配的路由起个名字,见名知意
    url(r'^register/', views.RegisterView.as_view(), name='register'),
]