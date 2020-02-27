from django.urls import path
from . import views

app_name = 'alexieui'

urlpatterns = [
    path('', views.index, name='index'),
    path('addform/<int:presetid>/', views.addform, name='addform'),
    path('add', views.add, name='add'),
]
