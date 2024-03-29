from django.conf.urls import url
from . import views

urlpatterns = [
    # url(r'^$', views.  )
    # 这里可以给匹配的路由起个名字,见名知意
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view(), name='list'),
    url(r'^hot/(?P<category_id>\d+)/$', views.HotView.as_view(), name='hot'),
    url(r'^detail/(?P<sku_id>\d+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^detail/visit/(?P<category_id>\d+)/$', views.VisitCategoryView.as_view(), name='visit'),

]