from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('venues/', views.VenueListView.as_view(), name='venues'),
    path('trips/', views.TripListView.as_view(), name='trips'),
    path('catches/', views.CatchListView.as_view(), name='catches'),
    path('catch/<int:pk>', views.CatchDetailView.as_view(), name='catch-detail'),
    path('trip/<int:pk>', views.TripDetailView.as_view(), name='trip-detail'),
    path('venue/<int:pk>', views.VenueDetailView.as_view(), name='venue-detail'),
]
