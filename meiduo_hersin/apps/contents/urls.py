from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^index/', views.IndexView.as_view(), name='index'),
    url(r'^carts/simple/', views.SimpleCartsView.as_view(), name='simplecarts'),

]