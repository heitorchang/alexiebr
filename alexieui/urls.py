from django.urls import path
from . import views

app_name = 'alexieui'

urlpatterns = [
    path('', views.index, name='index'),
    path('addform/<int:presetid>/', views.addform, name='addform'),
    path('add', views.add, name='add'),
    path('hist/', views.hist, name='hist'),
    path('acct/<int:acctid>/', views.acctdetail, name='acctdetail'),
    path('adj/<int:acctid>/', views.adj, name='adj'),
    path('budget/', views.budget, name='budget'),
    path('search/', views.search, name='search'),
    path('addfixed/<int:debitid>/<int:creditid>/', views.addfixed, name='addfixed'),
]
