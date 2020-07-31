from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catch/<int:pk>', views.CatchDetailView.as_view(), name='catch-detail'),
    path('catch/new/', views.CatchCreateView.as_view(), name='catch_new'),
    path('catch/<int:pk>/edit/', views.CatchUpdateView.as_view(), name='catch_edit'),
    path('catch/<int:pk>/delete/', views.CatchDeleteView.as_view(), name='catch_delete'),
    path('catches/', views.CatchListView.as_view(), name='catches'),
    path('fish/<int:pk>/edit/', views.FishUpdateView.as_view(), name='fish_edit'),
    path('fish/<int:pk>', views.FishDetailView.as_view(), name='fish-detail'),
    path('fish/new/', views.FishCreateView.as_view(), name='fish_new'),
    path('fish/<int:pk>/delete/', views.FishDeleteView.as_view(), name='fish_delete'),
    path('fishes/', views.FishListView.as_view(), name='fishes'),
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
