from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('backups/', views.BackupListView.as_view(), name='backups'),
]

