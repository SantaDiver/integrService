from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'siteHandler$', views.siteHandler, name='siteHandler'),
    url(r'cacheUpdate$', views.cacheUpdate, name='cacheUpdate'),
    url(r'configurator$', views.configurator, name='configurator'),
]
