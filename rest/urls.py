"""rest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework import routers

from rest.disasters import views
import rest_framework.authtoken.views as rest_views


router = routers.DefaultRouter()
#router.register(r'images', views.ImageViewSet, 'Image')
router.register(r'samples', views.SampleViewSet, 'Sample')

urlpatterns = [
    
    url(r'^', include(router.urls)),
    url(r'^images/$', views.ImageList.as_view()),
    url(r'^allimages/$', views.ImageAllList.as_view()),
    url(r'^debris/$', views.DebrisList.as_view()),
    url(r'^images/(?P<pk>[0-9]+)/(?P<x>[0-9]+)/(?P<y>[0-9]+)/(?P<w>[0-9]+)/(?P<h>[0-9]+)$', views.ImageDetail.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', rest_views.obtain_auth_token)
]
