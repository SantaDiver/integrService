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
from django.contrib.auth.views import logout
from django.conf import settings

from requestsHandler import views as requestsHandler_views

urlpatterns = [
    url(r'^su/', include('django_su.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^requestsHandler/', include('requestsHandler.urls')),
    url(r'siteHandler$', requestsHandler_views.siteHandler, name='siteHandler'),
    url(r'setConfig', requestsHandler_views.setConfig, name='setConfig'),
    url(r'getConfig', requestsHandler_views.getConfig, name='getConfig'),
    url(r'login', requestsHandler_views.login_user, name='login'),
    url(r'logout', logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'newForm', requestsHandler_views.newForm, name='newForm'),
    url(r'deleteForm', requestsHandler_views.deleteForm, name='deleteForm'),
    url(r'test', requestsHandler_views.test, name='test'),
    url(r'^\w*/{0,1}\w*$', requestsHandler_views.configurator, name='configurator'),
]
