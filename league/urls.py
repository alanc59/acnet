from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('PL', views.PLListView.as_view(), name='PL'),
    path('CH', views.CHListView.as_view(), name='CH'),
]

