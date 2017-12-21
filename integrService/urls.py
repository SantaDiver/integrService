"""integrService URL Configuration

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
from django.contrib import admin

from requestsHandler import views as requestsHandler_views

urlpatterns = [
    url(r'^$', requestsHandler_views.configurator, name='configurator'),
    url(r'^admin/', admin.site.urls),
    url(r'^requestsHandler/', include('requestsHandler.urls')),
    url(r'siteHandler$', requestsHandler_views.siteHandler, name='siteHandler'),
    url(r'cacheUpdate$', requestsHandler_views.cacheUpdate, name='cacheUpdate'),
    url(r'setConfig', requestsHandler_views.setConfig, name='setConfig'),
    url(r'getSchema', requestsHandler_views.getSchema, name='getSchema'),
]
