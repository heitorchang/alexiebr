from django.urls import path
from . import views

app_name = 'alexieui'

urlpatterns = [
    path('', views.index),
]

