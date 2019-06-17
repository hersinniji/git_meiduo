from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^qq/login/$', views.QQAuthUserView.as_view()),
]