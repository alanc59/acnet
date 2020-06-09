from django.shortcuts import render

# Create your views here.

from fishy.models import Bait, Catch, Fish, Trip, Venue

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_venues = Venue.objects.all().count()
    num_trips = Trip.objects.all().count()
    num_catches = Catch.objects.all().count() 
    
    context = {
        'num_venues': num_venues,
        'num_trips': num_trips,
        'num_catches': num_catches,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

from django.views import generic

class TripListView(generic.ListView):
    model = Trip
    paginate_by = 8

class VenueListView(generic.ListView):
    model = Venue
    paginate_by = 8

class CatchListView(generic.ListView):
    model = Catch
    paginate_by = 8

class CatchDetailView(generic.DetailView):
    model = Catch

class TripDetailView(generic.DetailView):
    model = Trip

class VenueDetailView(generic.DetailView):
    model = Venue
