from django.urls import path
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.views import login, logout_then_login
from accounts.views import Index
#from . import views
from rakumo import views

app_name = 'accounts'

urlpatterns = [
    #path('', views.index, name='index'),
    #path('group/', views.group, name='group'),
    #path('form/', views.form, name='form'),
    #path('complete/', views.complete, name='complete'),
    path('login/', views.login, {'template_name': 'accounts/login.html'}, name='login'),
    path('logout/', views.logout_then_login, name='logout'),
    path('index/', Index.as_view(), name='account_index'),
]
