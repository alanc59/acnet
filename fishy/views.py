from django.shortcuts import render
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy

from fishy.models import Bait, Catch, Fish, Trip, Venue
from util.utilities import *

from django.db.models import Sum, Count
from django.db.models.functions import Coalesce

from datetime import datetime, timedelta, timezone
from django.utils.timezone import localdate

import os
import logging
 
from django.contrib import messages
from django.contrib.auth import get_user_model
from PIL import Image, ImageOps
 
logger = logging.getLogger(__name__)

PHOTO_DIR = os.environ['PHOTO_DIR']


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Admins only (users with 'Staff status' ticked in Django admin).

    Visitors who aren't logged in are sent to the login page;
    logged-in users who aren't admins get a 403 Forbidden page.
    """

    def test_func(self):
        return self.request.user.is_staff

# ============================================================
#
# Index
#
# ============================================================

# Until multi-user adds an owner to Trip, every trip belongs to the
# single angler. Once Trip has a 'user' field this picks it up automatically.
TRIP_HAS_OWNER = any(f.name == 'user' for f in Trip._meta.get_fields())


def _anglers():
    """Active anglers: users who are not admins (staff / superusers)."""
    return (
        get_user_model().objects
        .filter(is_active=True, is_staff=False, is_superuser=False)
        .order_by('username')
    )


def _angler_name(user):
    return user.get_full_name() or user.get_username()


def _trips_for(user):
    if TRIP_HAS_OWNER:
        return Trip.objects.filter(user=user)
    return Trip.objects.all()


def index(request):
    """View function for home page of site."""

    # Calendar periods, in UK time
    today = localdate()
    year_start = today.replace(month=1, day=1)
    month_start = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())     # Monday

    anglers = list(_anglers())

    # ---- This year's record per angler (trips up to today) ----
    anglers_table = []
    for angler in anglers:
        trips = _trips_for(angler).filter(date__gte=year_start, date__lte=today)
        trip_count = trips.count()
        venue_count = trips.exclude(venue=None).values('venue').distinct().count()
        catches = Catch.objects.filter(trip__in=trips)
        fish_count = catches.count()
        total_weight = catches.aggregate(total=Sum('weight'))['total'] or 0

        anglers_table.append({
            'name': _angler_name(angler),
            'trips': trip_count,
            'venues': venue_count,
            'fish': fish_count,
            'total_weight': toPoundsAndOunces(total_weight),
            'avg_fish': round(fish_count / trip_count) if trip_count else 0,
            'avg_weight': toPoundsAndOunces(round(total_weight / trip_count) if trip_count else 0),
        })

    # ---- Fish of the week / month / year: heaviest WEIGHED fish ----
    def heaviest_since(start):
        return (
            Catch.objects
            .filter(weighed='Y', trip__date__gte=start, trip__date__lte=today)
            .select_related('fish', 'trip', 'trip__venue')
            .order_by('-weight', 'trip__date', 'catch_time')
            .first()
        )

    def angler_for(catch):
        if TRIP_HAS_OWNER and getattr(catch.trip, 'user', None):
            return _angler_name(catch.trip.user)
        if len(anglers) == 1:
            return anglers[0] and _angler_name(anglers[0])
        return ''

    fish_of = []
    for label, start, period, empty in (
        ('Week', week_start, 'Week starting ' + week_start.strftime('%-d %B'), 'this week'),
        ('Month', month_start, month_start.strftime('%B %Y'), 'this month'),
        ('Year', year_start, str(today.year), 'this year'),
    ):
        catch = heaviest_since(start)
        fish_of.append({
            'label': label,
            'period': period,
            'empty': empty,
            'catch': catch,
            'angler': angler_for(catch) if catch else '',
        })

    context = {
        'this_year': today.year,
        'anglers_table': anglers_table,
        'fish_of': fish_of,
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

        # Today's date in UK time (settings.TIME_ZONE), not UTC, so the
        # status doesn't lag by an hour around midnight in summer
        today = localdate()

        live_trip = (
            trip.date == today
        )

        future_trip = (
            trip.date > today
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
        context["future_trip"] = future_trip
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catch_count'] = self.object.catch_set.count()
        return context

    def form_valid(self, form):
        # The trip's catches are deleted with it (on_delete=CASCADE on
        # Catch.trip). Note which ones had photos first, then remove the
        # photo files once the database delete has succeeded.
        photo_ids = list(
            self.object.catch_set
            .filter(photo='Y')
            .values_list('id', flat=True)
        )

        response = super().form_valid(form)

        for catch_id in photo_ids:
            try:
                os.remove(os.path.join(PHOTO_DIR, f'{catch_id}.jpg'))
            except FileNotFoundError:
                pass
            except OSError:
                logger.exception('Could not delete photo for catch %s', catch_id)

        return response


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

def save_catch_photo(uploaded_file, catch_id):
    """Fix rotation, shrink, and save the photo as <catch_id>.jpg."""
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)   # stops phone photos appearing sideways
    img = img.convert('RGB')
    img.thumbnail((1600, 1600))          # max 1600px on the long side
    img.save(os.path.join(PHOTO_DIR, f'{catch_id}.jpg'), 'JPEG', quality=85)

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

        # Set when opened from a trip page's "New Catch" button (?trip=<id>),
        # so that trip is already selected in the dropdown
        context['selected_trip'] = self.request.GET.get('trip', '')

        return context

    def get_success_url(self):
        # Opened from a trip page: go back to that trip after saving,
        # otherwise show the new catch as before
        if self.request.POST.get('from_trip') and self.object.trip:
            return self.object.trip.get_absolute_url()
        return super().get_success_url()

    def form_valid(self, form):
        # Save the catch first so a problem with the photo never loses the entry
        response = super().form_valid(form)
 
        photo = self.request.FILES.get('photo')
        if photo:
            try:
                save_catch_photo(photo, self.object.pk)
                self.object.photo = 'Y'
                self.object.save(update_fields=['photo'])
            except Exception:
                logger.exception('Photo upload failed for catch %s', self.object.pk)
                messages.warning(
                    self.request,
                    'Catch saved, but the photo could not be processed.'
                )
 
        return response

class CatchUpdateView(LoginRequiredMixin, UpdateView):
    model = Catch
    template_name = 'fishy/catch_edit.html'
    fields = [
        'trip',
        'catch_time',
        'fish',
        'weight',
        'weighed',
        'bait',
        'method'
    ]
 
    def get_context_data(self, **kwargs):
 
        context = super().get_context_data(**kwargs)
 
        # Built fresh on every request so new trips, fish and baits
        # always appear in the dropdowns
        context['trips'] = (
            Trip.objects.all().order_by('-id')
        )
 
        context['fishes'] = (
            Fish.objects.all().order_by('name')
        )
 
        context['baits'] = (
            Bait.objects.all().order_by('name')
        )
 
        return context
 
    def form_valid(self, form):
        # Save the catch changes first so a problem with the photo never loses them
        response = super().form_valid(form)
 
        # Only act if a new photo was chosen; otherwise leave any existing
        # photo and the indicator exactly as they are
        photo = self.request.FILES.get('photo')
        if photo:
            try:
                save_catch_photo(photo, self.object.pk)   # overwrites <id>.jpg
                self.object.photo = 'Y'
                self.object.save(update_fields=['photo'])
            except Exception:
                logger.exception('Photo upload failed for catch %s', self.object.pk)
                messages.warning(
                    self.request,
                    'Catch updated, but the photo could not be processed.'
                )
 
        return response


class CatchDeleteView(LoginRequiredMixin, DeleteView):
    model = Catch
    template_name = 'fishy/catch_delete.html'
    success_url = reverse_lazy('catches')

    def form_valid(self, form):
        # Note the photo before the catch is deleted, then remove the
        # photo file once the database delete has succeeded
        catch_id = self.object.pk
        had_photo = (self.object.photo == 'Y')

        response = super().form_valid(form)

        if had_photo:
            try:
                os.remove(os.path.join(PHOTO_DIR, f'{catch_id}.jpg'))
            except FileNotFoundError:
                pass
            except OSError:
                logger.exception('Could not delete photo for catch %s', catch_id)

        return response


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


class FishCreateView(StaffRequiredMixin, CreateView):
    model = Fish
    template_name = "fishy/fish_new.html"
    fields = ["name", "latin_name", "uk_record"]


class FishDeleteView(StaffRequiredMixin, DeleteView):
    model = Fish
    template_name = "fishy/fish_delete.html"
    success_url = reverse_lazy("fishes")


class FishUpdateView(StaffRequiredMixin, UpdateView):
    model = Fish
    template_name = "fishy/fish_edit.html"
    fields = ["name", "latin_name", "uk_record"]

# ============================================================
#
# Bait
#
# Anyone can view baits; logged-in users can add and delete them.
#
# ============================================================

class BaitListView(generic.ListView):
    model = Bait

    def get_queryset(self):

        return (
            Bait.objects
            .annotate(
                catch_count=Count("catch")
            )
            .order_by("name")
        )


class BaitDetailView(generic.DetailView):
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

