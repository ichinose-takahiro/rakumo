from django.urls import path

#from . import views
from rakumo import views

app_name = 'rakumo'

urlpatterns = [
    path('', views.index, name='index'),
    #path('group/', views.group, name='group'),
    path('form/', views.form, name='form'),
    path('complete/', views.complete, name='complete'),
]
