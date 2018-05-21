from django.conf.urls import url,include

from rakumo import views

import os
#from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from django.contrib.auth.views import login,logout
from django.views.static import serve

app_name = 'rakumo'

urlpatterns = [
    #url('', views.index, name='index'),
    url('form/', views.form, name='form'),
    url('bp/', views.bp, name='bp'),
    #url('complete/', views.complete, name='complete'),
    url(r'^$', views.index, name='index'),

    url(r'^oauth2callback', views.auth_return),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', login,
                        {'template_name': 'rakumo/login.html'}, name='login'),
    url(r'^accounts/logout/$', logout,
        {'template_name': 'rakumo/logout.html'}, name='logout'),
    url(r'^static/(?P<path>.*)$', serve,
        {'document_root': os.path.join(os.path.dirname(__file__), 'static')}),
    url('readme/', views.readme, name='readme'),
]
