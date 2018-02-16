"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import include, url
from django.contrib.auth.views import login
from django.views.static import serve
import rakumo
admin.autodiscover()

import os
urlpatterns = [
    url('rakumo/', include('rakumo.urls')),
    #url('admin/', admin.site.urls),

    url(r'^oauth2callback', rakumo.views.auth_return),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', login,
                        {'template_name': 'rakumo/login.html'},name='login'),

    url(r'^static/(?P<path>.*)$', serve,
        {'document_root': os.path.join(os.path.dirname(__file__), 'static')}),
]
