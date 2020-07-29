from django.shortcuts import render
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from fishy.models import Bait, Catch, Fish, Trip, Venue

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_venues = Venue.objects.all().count()
    num_trips = Trip.objects.all().count()
    num_catches = Catch.objects.all().count() 

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    
    context = {
        'num_venues': num_venues,
        'num_trips': num_trips,
        'num_catches': num_catches,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

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

from util.utilities import *
from django.db.models import Sum
class TripDetailView(generic.DetailView):
    model = Trip
    paginate_by = 8
    
    def get_context_data(self, **kwargs):
        context = super(TripDetailView, self).get_context_data(**kwargs)
        catches = Catch.objects.filter(trip_id=self.kwargs.get('pk'))
        wgt = catches.aggregate(Sum('weight'))
        if wgt['weight__sum'] == None:
            wgt['weight__sum'] = 0   
        weight = toPoundsAndOunces(wgt['weight__sum'])
        context['weight'] = weight
        return context

class VenueDetailView(generic.DetailView):
    model = Venue

class VenueCreateView(CreateView):
    model = Venue
    template_name = 'fishy/venue_new.html'
    fields = ['name', 'wac', 'postcode']

class VenueUpdateView(UpdateView):
    model = Venue
    template_name = 'fishy/venue_edit.html'
    fields =['wac', 'postcode']

class TripUpdateView(UpdateView):
    model = Trip
    template_name = 'fishy/trip_edit.html'
    fields =['venue', 'date']
    venues = Venue.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venues'] = self.venues
        return context

class CatchUpdateView(UpdateView):
    model = Catch
    template_name = 'fishy/catch_edit.html'
    fields =['trip', 'fish', 'weight', 'weighed', 'bait', 'method']
    trips = Trip.objects.all().order_by('-id')
    fishes = Fish.objects.all().order_by('name')
    baits = Bait.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trips'] = self.trips
        context['fishes'] = self.fishes
        context['baits'] = self.baits
        return context

class TripCreateView(CreateView):
    model = Trip
    template_name = 'fishy/trip_new.html'
    fields = ['venue', 'date']
    venues = Venue.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venues'] = self.venues
        return context

class CatchCreateView(CreateView):
    model = Catch
    template_name = 'fishy/catch_new.html'
    fields = ['trip', 'fish', 'weight', 'weighed', 'bait', 'method']
    trips = Trip.objects.all().order_by('-date')
    fishes = Fish.objects.all().order_by('name')
    baits = Bait.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trips'] = self.trips
        context['fishes'] = self.fishes
        context['baits'] = self.baits
        return context

class CatchDeleteView(DeleteView):
    model = Catch
    template_name = 'fishy/catch_delete.html'
    success_url = reverse_lazy('catches')

class VenueDeleteView(DeleteView):
    model = Venue
    template_name = 'fishy/venue_delete.html'
    success_url = reverse_lazy('venues')

class TripDeleteView(DeleteView):
    model = Trip
    template_name = 'fishy/trip_delete.html'
    success_url = reverse_lazy('trips')
