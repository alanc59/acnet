from django.shortcuts import render
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from fishy.models import Bait, Catch, Fish, Trip, Venue
from util.utilities import *

from django.db.models import Sum, Count
from django.db.models.functions import Coalesce

from datetime import datetime, timedelta, timezone

import os


# ============================================================
#
# Index
#
# ============================================================

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
    return render(
        request,
        'fishy/index.html',
        context=context
    )


# ============================================================
#
# Trip
#
# ============================================================

class TripListView(generic.ListView):
    model = Trip

    def get_queryset(self):

        venue_id = self.request.GET.get("venue")

        queryset = (
            Trip.objects
            .select_related("venue")
            .annotate(
                fish_count=Count("catch"),
                total_weight=Coalesce(
                    Sum("catch__weight"),
                    0
                )
            )
            .order_by("-date")
        )

        if venue_id:
            queryset = queryset.filter(
                venue_id=venue_id
            )

        return queryset

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        venue_id = self.request.GET.get("venue")

        # These two lines are needed for the dropdown
        context["venues"] = Venue.objects.order_by("name")
        context["selected_venue"] = venue_id

        if venue_id:

            venue = Venue.objects.get(
                pk=venue_id
            )

            context["subtitle"] = (
                f"Fishing trips recorded: "
                f"{context['object_list'].count()} "
                f"({venue.name})"
            )

        else:

            context["subtitle"] = (
                f"Fishing trips recorded: "
                f"{Trip.objects.count()} "
                f"(All venues)"
            )

        context["trip_count"] = (
            context["object_list"].count()
        )

        return context


class TripDetailView(generic.DetailView):
    model = Trip

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        trip = self.object

        catches = (
            Catch.objects
            .filter(trip=trip)
            .select_related("fish", "bait")
            .order_by("-catch_time")
        )

        time_now = datetime.now(timezone.utc)

        live_trip = (
            trip.date == time_now.date()
        )

        latest_catch = catches.first()

        new_fish = (
            latest_catch is not None
            and
            latest_catch.catch_time >=
            time_now - timedelta(minutes=10)
        )

        total_weight_oz = (
            catches.aggregate(
                total=Sum("weight")
            )["total"] or 0
        )

        catch_count = catches.count()

        if catch_count:
            average_weight = round(
                total_weight_oz / catch_count
            )
        else:
            average_weight = 0

        context["catch_count"] = catch_count

        context["weight"] = (
            toPoundsAndOunces(total_weight_oz)
        )

        context["avg_weight"] = (
            toPoundsAndOunces(average_weight)
        )

        context["live_trip"] = live_trip
        context["new_fish"] = new_fish
        context["latest_catch"] = latest_catch

        return context


class TripCreateView(LoginRequiredMixin, CreateView):
    model = Trip
    template_name = 'fishy/trip_new.html'
    fields = ['venue', 'date']

    venues = Venue.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['venues'] = self.venues

        return context


class TripUpdateView(LoginRequiredMixin, UpdateView):
    model = Trip
    template_name = 'fishy/trip_edit.html'
    fields = ['venue', 'date']

    venues = Venue.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['venues'] = self.venues

        return context


class TripDeleteView(LoginRequiredMixin, DeleteView):
    model = Trip
    template_name = 'fishy/trip_delete.html'
    success_url = reverse_lazy('trips')


# ============================================================
#
# Venue
#
# ============================================================

class VenueListView(generic.ListView):
    model = Venue

    def get_queryset(self):

        return (
            Venue.objects
            .annotate(
                total_visits=Count(
                    "trip",
                    distinct=True
                ),
                total_fish=Count(
                    "trip__catch",
                    distinct=True
                ),
                total_weight=Coalesce(
                    Sum("trip__catch__weight"),
                    0
                )
            )
            .order_by("name")
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        for venue in context["venue_list"]:

            venue.total_weight_display = (
                toPoundsAndOunces(
                    venue.total_weight
                )
            )

        return context


class VenueDetailView(generic.DetailView):
    model = Venue

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        venue = self.object

        trips = Trip.objects.filter(
            venue=venue
        )

        total_visits = trips.count()

        catches = Catch.objects.filter(
            trip__venue=venue
        )

        total_fish = catches.count()

        total_weight = (
            catches.aggregate(
                total=Sum("weight")
            )["total"] or 0
        )

        context["total_visits"] = total_visits
        context["total_fish"] = total_fish
        context["total_weight"] = (
            toPoundsAndOunces(total_weight)
        )

        return context


class VenueCreateView(LoginRequiredMixin, CreateView):
    model = Venue
    template_name = 'fishy/venue_new.html'
    fields = ['name', 'wac', 'postcode']


class VenueUpdateView(LoginRequiredMixin, UpdateView):
    model = Venue
    template_name = 'fishy/venue_edit.html'
    fields = ['wac', 'postcode']


class VenueDeleteView(LoginRequiredMixin, DeleteView):
    model = Venue
    template_name = 'fishy/venue_delete.html'
    success_url = reverse_lazy('venues')


# ============================================================
#
# Catch
#
# ============================================================

class CatchListView(generic.ListView):
    model = Catch
    template_name = "fishy/catch_list.html"

    def get_queryset(self):

        venue_id = self.request.GET.get("venue")
        fish_id = self.request.GET.get("fish")
        method = self.request.GET.get("method")
        photo = self.request.GET.get("photo")
        bait_id = self.request.GET.get("bait")

        queryset = (
            Catch.objects
            .select_related(
                "trip",
                "trip__venue",
                "fish",
                "bait",
            )
            .order_by(
                "-trip__date",
                "-id"
            )
        )

        if venue_id:
            queryset = queryset.filter(
                trip__venue_id=venue_id
            )

        if fish_id:
            queryset = queryset.filter(
                fish_id=fish_id
            )

        if method:
            queryset = queryset.filter(
                method=method
            )

        if photo:
            queryset = queryset.filter(
                photo=photo
            )

        if bait_id:
            queryset = queryset.filter(
                bait_id=bait_id
            )

        return queryset

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["venues"] = (
            Venue.objects.order_by("name")
        )

        context["fishes"] = (
            Fish.objects.order_by("name")
        )

        context["baits"] = (
            Bait.objects.order_by("name")
        )

        context["selected_venue"] = (
            self.request.GET.get("venue", "")
        )

        context["selected_fish"] = (
            self.request.GET.get("fish", "")
        )

        context["selected_method"] = (
            self.request.GET.get("method", "")
        )

        context["selected_photo"] = (
            self.request.GET.get("photo", "")
        )

        context["selected_bait"] = (
            self.request.GET.get("bait", "")
        )

        context["subtitle"] = (
            f"Fish recorded: "
            f"{context['object_list'].count()}"
        )

        return context


class CatchDetailView(generic.DetailView):
    model = Catch

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        catch = self.object

        context["weight_display"] = (
            toPoundsAndOunces(catch.weight)
        )

        return context


class CatchCreateView(LoginRequiredMixin, CreateView):
    model = Catch
    template_name = 'fishy/catch_new.html'
    fields = [
        'trip',
        'fish',
        'weight',
        'weighed',
        'bait',
        'method'
    ]

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['trips'] = (
            Trip.objects.order_by('-date')
        )

        context['fishes'] = (
            Fish.objects.order_by('name')
        )

        context['baits'] = (
            Bait.objects.order_by('name')
        )

        return context


class CatchUpdateView(LoginRequiredMixin, UpdateView):
    model = Catch
    template_name = 'fishy/catch_edit.html'
    fields = [
        'trip',
        'fish',
        'weight',
        'weighed',
        'bait',
        'method'
    ]

    trips = (
        Trip.objects.all().order_by('-id')
    )

    fishes = (
        Fish.objects.all().order_by('name')
    )

    baits = (
        Bait.objects.all().order_by('name')
    )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['trips'] = self.trips
        context['fishes'] = self.fishes
        context['baits'] = self.baits

        return context


class CatchDeleteView(LoginRequiredMixin, DeleteView):
    model = Catch
    template_name = 'fishy/catch_delete.html'
    success_url = reverse_lazy('catches')


# ============================================================
#
# Fish
#
# ============================================================

class FishListView(generic.ListView):
    model = Fish

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        fishes = Fish.objects.all().order_by("name")

        for fish in fishes:
            fish.uk_record = toPoundsAndOunces(fish.uk_record)

        context["fishes"] = fishes

        return context


class FishDetailView(generic.DetailView):
    model = Fish

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        fish = self.object

        # UK record
        context["uk_record"] = toPoundsAndOunces(
            fish.uk_record
        )

        # Find the user's best catch of this species
        best_catch = (
            Catch.objects
            .filter(fish=fish)
            .select_related(
                "trip",
                "trip__venue",
            )
            .order_by("-weight")
            .first()
        )

        if best_catch:
            context["best_catch"] = best_catch
            context["best_catch_weight"] = toPoundsAndOunces(
                best_catch.weight
            )
        else:
            context["best_catch"] = None
            context["best_catch_weight"] = None

        return context


class FishCreateView(CreateView):
    model = Fish
    template_name = "fishy/fish_new.html"
    fields = ["name", "latin_name", "uk_record"]


class FishDeleteView(DeleteView):
    model = Fish
    template_name = "fishy/fish_delete.html"
    success_url = reverse_lazy("fishes")


class FishUpdateView(UpdateView):
    model = Fish
    template_name = "fishy/fish_edit.html"
    fields = ["name", "latin_name", "uk_record"]

# ============================================================
#
# Bait
#
# Bait is completely protected.
#
# ============================================================

class BaitListView(LoginRequiredMixin, generic.ListView):
    model = Bait


class BaitDetailView(LoginRequiredMixin, generic.DetailView):
    model = Bait


class BaitCreateView(LoginRequiredMixin, CreateView):
    model = Bait
    template_name = 'fishy/bait_new.html'
    fields = ['name']


class BaitDeleteView(LoginRequiredMixin, DeleteView):
    model = Bait
    template_name = 'fishy/bait_delete.html'
    success_url = reverse_lazy('baits')


# ============================================================
#
# Reports
#
# ============================================================

def statistics_report(request, report_name):

    report_file = os.path.join(
        os.getenv("FISHY_STATS_DIR"),
        report_name
    )

    if os.path.exists(report_file):

        with open(report_file, "r") as f:
            report_html = f.read()

    else:

        report_html = (
            '<div class="report-card">'
            '<h1 class="report-title">'
            '<span class="line"></span>'
            'Report unavailable'
            '<span class="line"></span>'
            '</h1>'
            '<p class="text-center">'
            'The statistics report has not yet been generated.'
            '</p>'
            '</div>'
        )

    return render(
        request,
        "fishy/statistics_report.html",
        {
            "report_html": report_html,
        }
    )