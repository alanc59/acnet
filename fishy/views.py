from django.shortcuts import render
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from fishy.models import Bait, Catch, Fish, Trip, Venue
from util.utilities import *
from django.db.models import Sum
from datetime import datetime, timedelta, timezone

#######
#
# index
#
#######
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
    return render(request, 'fishy/index.html', context=context)

#######
#
# Trip
#
#######

class TripListView(generic.ListView):
    model = Trip
    paginate_by = 8

class TripDetailView(generic.DetailView):
    model = Trip
    paginate_by = 8

    def get_context_data(self, **kwargs):
        context = super(TripDetailView, self).get_context_data(**kwargs)
        trips = Trip.objects.filter(id=self.kwargs.get('pk'))
        for trip in trips:
            catch_date = trip.date.strftime('%Y-%m-%d')
        catches = Catch.objects.filter(trip_id=self.kwargs.get('pk'))
        new_fish = False
        time_now = datetime.now(timezone.utc)

        for catch in catches:
            catch_date = catch.trip.date.strftime('%Y-%m-%d')
            new_time = time_now - timedelta(minutes=10)
            if new_time <= catch.catch_time:
                new_fish = True
            break
        today_date = time_now.strftime('%Y-%m-%d')
        live_trip = (catch_date == today_date)
        wgt = catches.aggregate(Sum('weight'))
        if wgt['weight__sum'] == None:
            wgt['weight__sum'] = 0   
        weight = toPoundsAndOunces(wgt['weight__sum'])
        context['weight'] = weight
        context['live_trip'] = live_trip
        context['new_fish'] = new_fish
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

class TripUpdateView(UpdateView):
    model = Trip
    template_name = 'fishy/trip_edit.html'
    fields =['venue', 'date']
    venues = Venue.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['venues'] = self.venues
        return context

class TripDeleteView(DeleteView):
    model = Trip
    template_name = 'fishy/trip_delete.html'
    success_url = reverse_lazy('trips')

#######
#
# Venue
#
#######

class VenueListView(generic.ListView):
    model = Venue
    paginate_by = 8

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

class VenueDeleteView(DeleteView):
    model = Venue
    template_name = 'fishy/venue_delete.html'
    success_url = reverse_lazy('venues')

#######
#
# Catch
#
#######

class CatchListView(generic.ListView):
    model = Catch
    paginate_by = 8

class CatchDetailView(generic.DetailView):
    model = Catch

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

class CatchDeleteView(DeleteView):
    model = Catch
    template_name = 'fishy/catch_delete.html'
    success_url = reverse_lazy('catches')

#######
#
# Fish
#
#######

class FishListView(generic.ListView):
    model = Fish
    fishes = Fish.objects.all().order_by('name')

    def get_context_data(self, *args, **kwargs):
        context = super(FishListView, self).get_context_data(*args, **kwargs)
        # add extra field
        for fish in self.fishes:
            fish.uk_record = toPoundsAndOunces(fish.uk_record)
        context["fishes"] = self.fishes
        return context


class FishDetailView(generic.DetailView):
    model = Fish

    def get_context_data(self, *args, **kwargs): 
        context = super(FishDetailView, self).get_context_data(*args, **kwargs) 
        my_object = self.get_object()
        # add extra field  
        context["uk_record"] = toPoundsAndOunces(my_object.uk_record)
        return context 

class FishCreateView(CreateView):
    model = Fish
    template_name = 'fishy/fish_new.html'
    fields = ['name', 'latin_name', 'uk_record']

class FishDeleteView(DeleteView):
    model = Fish
    template_name = 'fishy/fish_delete.html'
    success_url = reverse_lazy('fishes')

class FishUpdateView(UpdateView):
    model = Fish
    template_name = 'fishy/fish_edit.html'
    fields =['name', 'latin_name', 'uk_record']

#######
#
# Bait
#
#######

class BaitListView(generic.ListView):
    model = Bait
    paginate_by = 8

class BaitDetailView(generic.DetailView):
    model = Bait

class BaitCreateView(CreateView):
    model = Bait
    template_name = 'fishy/bait_new.html'
    fields = ['name']

class BaitDeleteView(DeleteView):
    model = Bait
    template_name = 'fishy/bait_delete.html'
    success_url = reverse_lazy('baits')
