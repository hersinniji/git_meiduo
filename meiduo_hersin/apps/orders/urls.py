from django.conf.urls import url
from . import views

urlpatterns = [
    # url(r'^$', views.  )
    # 这里可以给匹配的路由起个名字,见名知意
    url(r'^order/place/$', views.PlaceOrderView.as_view(), name='placeorder'),
    url(r'^orders/commit/$', views.OrderView.as_view(), name='commitorder'),
    url(r'^orders/success/$', views.OrderSuccessView.as_view(), name='ordersuccess'),
]