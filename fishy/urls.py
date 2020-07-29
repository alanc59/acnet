from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catch/<int:pk>', views.CatchDetailView.as_view(), name='catch-detail'),
    path('catch/new/', views.CatchCreateView.as_view(), name='catch_new'),
    path('catch/<int:pk>/edit/', views.CatchUpdateView.as_view(), name='catch_edit'),
    path('catch/<int:pk>/delete/', views.CatchDeleteView.as_view(), name='catch_delete'),
    path('catches/', views.CatchListView.as_view(), name='catches'),
    path('trip/<int:pk>/edit/', views.TripUpdateView.as_view(), name='trip_edit'),
    path('trip/<int:pk>', views.TripDetailView.as_view(), name='trip-detail'),
    path('trip/new/', views.TripCreateView.as_view(), name='trip_new'),
    path('trip/<int:pk>/delete/', views.TripDeleteView.as_view(), name='trip_delete'),
    path('trips/', views.TripListView.as_view(), name='trips'),
    path('venue/<int:pk>', views.VenueDetailView.as_view(), name='venue-detail'),
    path('venue/new/', views.VenueCreateView.as_view(), name='venue_new'),
    path('venue/<int:pk>/edit/', views.VenueUpdateView.as_view(), name='venue_edit'),
    path('venues/', views.VenueListView.as_view(), name='venues'),
    path('venue/<int:pk>/delete/', views.VenueDeleteView.as_view(), name='venue_delete'),
]
