from django.conf.urls import url
from . import views

urlpatterns = [
    # url(r'^$', views.  )
    # 这里可以给匹配的路由起个名字,见名知意
    url(r'^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view(), name='payment'),
    url(r'^payment/status/$', views.PaymentStatusView.as_view(), name='paymentstatus'),

]