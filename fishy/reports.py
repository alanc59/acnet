"""
Live statistics reports.

These replace the pre-built report files that the fishy_support cron job
used to write. Each report is worked out from the database when the page
is opened, so it is always up to date, and it can be shown for one angler
or for all anglers (the Angler filter at the top of each report).

The calculations follow the old fishy_support queries, and the HTML uses
the same structure and CSS classes, so the reports look the same as before.
"""
from collections import Counter, defaultdict
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.timezone import localdate, localtime

from fishy.models import Bait, Catch, Fish, Trip, Venue, angler_name
from util.utilities import toPoundsAndOunces

# Fish by Time: the old script used the stored (UTC) time, which put summer
# catches an hour early. True = use UK time (correct); False = old behaviour.
FISH_BY_TIME_UK_TIME = True

# Leave out rows that would be all zeros (species never caught, venues
# never fished, etc.). False = list everything, as the old reports did.
HIDE_EMPTY_ROWS = True

# Reports with this many year columns or fewer are shown at their natural
# width and centred, rather than stretched across the panel.
COMPACT_MAX_YEARS = 3

RECENT = "bg-info"      # trip in the last N days
LIVE = "bg-warning"     # today's trip
RECORD = "bg-success"   # all-time record


# ------------------------------------------------------------------
# Small helpers (same output as the old Report.th / Report.td)
# ------------------------------------------------------------------

def _cell(tag, text, cls, divider):
    if cls:
        attr = f'class="{cls} divider"' if divider else f'class="{cls}"'
    elif divider:
        attr = 'class="divider"'
    else:
        attr = ''
    return f"<{tag} {attr}>{text}</{tag}>"


def th(text="", cls="", divider=False):
    return _cell("TH", text, cls, divider)


def td(text="", cls="", divider=False):
    return _cell("TD", text, cls, divider)


def lbs_oz(oz):
    """'2-00' style, as used by the old records / top trips reports."""
    oz = int(oz or 0)
    return f"{oz // 16}-{oz % 16:02d}"


def dmy(d):
    return d.strftime("%d-%m-%Y")


def anglers():
    return (
        get_user_model().objects
        .filter(is_active=True, is_staff=False, is_superuser=False)
        .order_by("username")
    )


def selected_angler(request):
    value = request.GET.get("angler")
    if value is None:
        value = str(request.user.pk) if request.user.is_authenticated else ""
    return value if value.isdigit() else ""


# ------------------------------------------------------------------
# Data for one report (one angler, or everyone)
# ------------------------------------------------------------------

class Data:
    def __init__(self, angler_id):
        self.all_anglers = not angler_id

        trips = Trip.objects.select_related("venue", "user")
        catches = (
            Catch.objects
            .filter(trip__isnull=False)
            .select_related("trip", "trip__venue", "fish", "bait", "user")
        )
        venues = Venue.objects.all()
        baits = Bait.objects.all()

        if angler_id:
            trips = trips.filter(user_id=angler_id)
            catches = catches.filter(user_id=angler_id)
            venues = venues.filter(user_id=angler_id)
            baits = baits.filter(user_id=angler_id)

        self.trips = list(trips)
        self.catches = list(catches)
        self.years = sorted({t.date.year for t in self.trips}, reverse=True)
        self.compact = len(self.years) <= COMPACT_MAX_YEARS
        self.fish_names = list(Fish.objects.order_by("name").values_list("name", flat=True))
        # With "All anglers", venues / baits of the same name are combined
        self.venue_names = sorted(set(venues.values_list("name", flat=True)))
        self.bait_names = sorted(set(baits.values_list("name", flat=True)))

    def venue_label(self, venue_name, user):
        """Venue name, plus the angler when showing everyone."""
        if self.all_anglers and user is not None:
            return f"{escape(venue_name)} ({escape(angler_name(user))})"
        return escape(venue_name)


# ------------------------------------------------------------------
# Page structure
# ------------------------------------------------------------------

def _filter_form(request, extra=""):
    current = selected_angler(request)
    options = ['<option value="">All anglers</option>']
    for a in anglers():
        sel = " selected" if str(a.pk) == current else ""
        options.append(f'<option value="{a.pk}"{sel}>{escape(angler_name(a))}</option>')
    return (
        '<form method="get" class="m-0">'
        '<div class="angler-filter">'
        '<label for="id_angler">Angler</label>'
        '<select name="angler" id="id_angler" onchange="this.form.submit();">'
        + "".join(options) +
        '</select>' + extra + '</div></form>\n'
    )


def _page(request, title, table_class, headers, body, note="", compact=False, extra_filter=""):
    wrapper = "table-wrapper compact-report" if compact else "table-wrapper"
    return (
        '<div class="report-card">\n'
        f'    <h1 class="report-title"><span class="line"></span>{title}<span class="line"></span></h1>\n'
        + _filter_form(request, extra_filter) +
        f'    <div class="{wrapper}">\n'
        f'        <table class="shared-report {table_class}">\n'
        '            <thead>\n' + headers + '            </thead>\n'
        '            <tbody>\n' + body + '            </tbody>\n'
        '        </table>\n'
        '    </div>\n'
        + note +
        '</div>\n'
    )


# ------------------------------------------------------------------
# The reports
# ------------------------------------------------------------------

def fish_by_species_by_year(request, d):
    headers = "<TR>" + th("Fish", "species-col") + th("Total", "total-col text-end")
    headers += "".join(th(y, "text-end") for y in d.years) + "</TR>\n"

    counts = Counter((c.fish.name if c.fish else None, c.trip.date.year) for c in d.catches)
    totals = Counter(c.fish.name if c.fish else None for c in d.catches)

    body = ""
    year_totals = Counter()
    grand = 0
    for name in d.fish_names:
        if HIDE_EMPTY_ROWS and not totals[name]:
            continue
        body += "<TR>" + th(escape(name), "species-col") + th(totals[name], "total-col text-end")
        grand += totals[name]
        for y in d.years:
            n = counts[(name, y)]
            year_totals[y] += n
            body += td(n, "text-end")
        body += "</TR>\n"
    body += "<TR>" + th("Totals", "text-end species-col") + th(grand, "total-col text-end")
    body += "".join(th(year_totals[y], "text-end") for y in d.years) + "</TR>\n"

    return _page(request, "Fish By Species By Year", "species-report", headers, body, compact=d.compact)


def fish_by_venue_by_year(request, d):
    headers = "<TR>" + th("Venue", "venue-col") + th("Total", "total-col text-end")
    headers += "".join(th(y, "text-end") for y in d.years) + "</TR>\n"

    counts = Counter((c.trip.venue.name if c.trip.venue else None, c.trip.date.year) for c in d.catches)
    totals = Counter(c.trip.venue.name if c.trip.venue else None for c in d.catches)

    body = ""
    year_totals = Counter()
    grand = 0
    for name in d.venue_names:
        if HIDE_EMPTY_ROWS and not totals[name]:
            continue
        body += "<TR>" + th(escape(name), "venue-col") + th(totals[name], "total-col text-end")
        grand += totals[name]
        for y in d.years:
            n = counts[(name, y)]
            year_totals[y] += n
            body += td(n, "text-end")
        body += "</TR>\n"
    body += "<TR>" + th("Totals", "venue-col") + th(grand, "total-col text-end")
    body += "".join(th(year_totals[y], "text-end") for y in d.years) + "</TR>\n"

    return _page(request, "Fish By Venue By Year", "venue-report", headers, body, compact=d.compact)


def fish_by_bait_by_year(request, d):
    headers = "<TR>" + th("Bait", "bait-col") + th("Total", "total-col text-end")
    headers += "".join(th(y, "text-end") for y in d.years) + "</TR>\n"

    counts = Counter((c.bait.name if c.bait else None, c.trip.date.year) for c in d.catches)
    totals = Counter(c.bait.name if c.bait else None for c in d.catches)

    body = ""
    year_totals = Counter()
    grand = 0
    for name in d.bait_names:
        if HIDE_EMPTY_ROWS and not totals[name]:
            continue
        body += "<TR>" + th(escape(name), "bait-col") + th(totals[name], "total-col text-end")
        grand += totals[name]
        for y in d.years:
            n = counts[(name, y)]
            year_totals[y] += n
            body += td(n, "text-end")
        body += "</TR>\n"
    body += "<TR>" + th("Totals", "bait-col") + th(grand, "total-col text-end")
    body += "".join(td(year_totals[y], "text-end") for y in d.years) + "</TR>\n"

    return _page(request, "Fish By Bait By Year", "bait-report", headers, body, compact=d.compact)


def fish_records(request, d):
    header1 = "<TR>" + th("&nbsp;", "fish-col") + th("All Time", "alltime-col text-center")
    header2 = "<TR>" + th("Fish", "text-start fish-col") + th("Record<BR>lbs-oz", "text-center alltime-col")
    for y in d.years:
        header1 += f'<TH colspan="3" class="text-center">{y}</TH>'
        header2 += th("Date", "text-start") + th("Venue", "text-center") + th("lbs-oz", "text-end")
    headers = header1 + "</TR>\n" + header2 + "</TR>\n"

    # Heaviest catch per fish (all time) and per fish per year; every fish
    # counts, weighed or estimated, as in the old report.
    best_all = {}
    best_year = {}
    for c in d.catches:
        if not c.fish:
            continue
        name, y = c.fish.name, c.trip.date.year
        if name not in best_all or c.weight > best_all[name]:
            best_all[name] = c.weight
        key = (name, y)
        cur = best_year.get(key)
        if cur is None or c.weight > cur.weight or (c.weight == cur.weight and c.trip.date < cur.trip.date):
            best_year[key] = c

    body = ""
    for name in d.fish_names:
        record = best_all.get(name)
        if HIDE_EMPTY_ROWS and record is None:
            continue
        body += "<TR>" + th(escape(name), "text-start fish-col")
        if record is None:
            body += th("", "alltime-col", True)
        else:
            body += th(lbs_oz(record), f"alltime-col text-center {RECORD}", True)
        for y in d.years:
            c = best_year.get((name, y))
            if c is None:
                body += td("", "", True) + td("") + td("")
                continue
            venue = d.venue_label(c.trip.venue.name if c.trip.venue else "", c.user)
            if c.weight == record:
                body += (th(dmy(c.trip.date), f"{RECORD} text-start", True)
                         + th(venue, f"{RECORD} text-center")
                         + th(lbs_oz(c.weight), f"{RECORD} text-end"))
            else:
                body += (td(dmy(c.trip.date), "text-start", True)
                         + td(venue, "text-center")
                         + td(lbs_oz(c.weight), "text-end"))
        body += "</TR>\n"

    return _page(request, "Fish Records", "record-report", headers, body, compact=d.compact)


def _top_trips(request, d, title, this_year_only, recent_days):
    today = localdate()
    trips = [t for t in d.trips if not this_year_only or t.date.year == today.year]
    trip_ids = {t.pk for t in trips}

    count = Counter()
    weight = Counter()
    for c in d.catches:
        if c.trip_id in trip_ids:
            count[c.trip_id] += 1
            weight[c.trip_id] += c.weight
    with_fish = [t for t in trips if count[t.pk] > 0]

    by_number = sorted(with_fish, key=lambda t: (-count[t.pk], -t.date.toordinal()))[:20]
    by_weight = sorted(with_fish, key=lambda t: (-weight[t.pk], -t.date.toordinal()))[:20]

    since = today - timedelta(days=recent_days)

    def cells(t, value):
        venue = d.venue_label(t.venue.name if t.venue else "", t.user)
        if t.date > since:
            colour = LIVE if t.date == today else RECENT
            return (td(dmy(t.date), f"{colour} text-center", True)
                    + td(venue, colour)
                    + td(value, f"{colour} text-center"))
        return td(dmy(t.date), "text-center", True) + td(venue, "") + td(value, "text-center")

    headers = "<TR>" + th("&nbsp;", "")
    headers += '<TH colspan="3" class="text-center">Fish By Number</TH><TH colspan="3" class="text-center">Fish By Weight</TH></TR>\n'
    headers += ("<TR>" + th("Position", "text-center") + th("Date", "text-center", True)
                + th("Venue", "text-start") + th("Fish", "text-center")
                + th("Date", "text-center", True) + th("Venue", "text-start")
                + th("Fish", "text-center") + "</TR>\n")

    body = ""
    for i in range(len(by_number)):
        body += "<TR>" + th(i + 1, "text-center")
        body += cells(by_number[i], count[by_number[i].pk])
        body += cells(by_weight[i], lbs_oz(weight[by_weight[i].pk]))
        body += "</TR>\n"
    if not by_number:
        body = '<TR><TD colspan="7" class="text-center">No trips with fish yet.</TD></TR>\n'

    note = ('<DIV class="report-note"><TABLE><TR>'
            + th("Colour indicates:", "") + td("Historic trip", "")
            + td(f"Trip in the last {recent_days} days", RECENT)
            + td("Current live trip", LIVE)
            + "</TR></TABLE></DIV>\n")

    return _page(request, title, "top-trips-report", headers, body, note)


def top_twenty_trips(request, d):
    return _top_trips(request, d, "Top Twenty Trips", False, 90)


def top_twenty_trips_this_year(request, d):
    return _top_trips(request, d, "Top Twenty Trips This Year", True, 14)


def trip_by_venue_by_year(request, d):
    header1 = "<TR>" + th("&nbsp;", "venue-col") + th("Total", "visit-col") + th("Total", "weight-col text-end")
    header2 = "<TR>" + th("Venue", "venue-col text-start") + th("Visits", "visit-col", True) + th("Weight", "weight-col text-end")
    for y in d.years:
        header1 += f'<TH colspan="2" class="text-center">{y}</TH>'
        header2 += th("Visits", "", True) + th("Weight", "text-end")
    headers = header1 + "</TR>\n" + header2 + "</TR>\n"

    visits = Counter()          # (venue, year) and (venue, None) for all years
    weights = Counter()
    for t in d.trips:
        name = t.venue.name if t.venue else None
        visits[(name, t.date.year)] += 1
        visits[(name, None)] += 1
    for c in d.catches:
        name = c.trip.venue.name if c.trip.venue else None
        weights[(name, c.trip.date.year)] += c.weight
        weights[(name, None)] += c.weight

    body = ""
    year_visits = Counter()
    year_weights = Counter()
    grand_visits = grand_weight = 0
    for name in d.venue_names:
        if HIDE_EMPTY_ROWS and not visits[(name, None)]:
            continue
        body += ("<TR>" + th(escape(name), "venue-col text-start")
                 + th(visits[(name, None)], "visit-col", True)
                 + th(toPoundsAndOunces(weights[(name, None)]), "weight-col text-end"))
        grand_visits += visits[(name, None)]
        grand_weight += weights[(name, None)]
        for y in d.years:
            year_visits[y] += visits[(name, y)]
            year_weights[y] += weights[(name, y)]
            body += td(visits[(name, y)], "", True) + td(toPoundsAndOunces(weights[(name, y)]), "text-end")
        body += "</TR>\n"
    body += ("<TR>" + th("Totals", "venue-col text-start")
             + th(grand_visits, "visit-col", True)
             + th(toPoundsAndOunces(grand_weight), "weight-col text-end"))
    for y in d.years:
        body += td(year_visits[y], "", True) + td(toPoundsAndOunces(year_weights[y]), "text-end")
    body += "</TR>\n"

    return _page(request, "Trips By Venue By Year", "trips-by-venue-report", headers, body, compact=d.compact)


def fish_by_time(request, d):
    hours = list(range(6, 20))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    headers = ("<TR>" + th("Month", "month-col") + th("Trips", "trips-col text-end")
               + th("Total Fish", "total-col text-end")
               + "".join(th(f"{h:02d}:00", "text-end", True) for h in hours) + "</TR>\n")

    trips_by_month = Counter(t.date.month for t in d.trips)
    month_total = Counter()
    month_hour = Counter()
    for c in d.catches:
        when = localtime(c.catch_time) if FISH_BY_TIME_UK_TIME else c.catch_time
        month_total[when.month] += 1
        month_hour[(when.month, when.hour)] += 1

    body = ""
    hour_totals = Counter()
    all_fish = 0
    for m in range(1, 13):
        body += ("<TR>" + td(months[m - 1], "month-col")
                 + td(trips_by_month[m], "trips-col text-end")
                 + td(month_total[m], "total-col text-end"))
        for h in hours:
            n = month_hour[(m, h)]
            hour_totals[h] += n
            all_fish += n
            body += td(n, "text-end", True)
        body += "</TR>"
    body += ("<TR>" + th("Totals", "month-col text-end")
             + th(len(d.trips), "trips-col text-end")
             + th(all_fish, "total-col text-end")
             + "".join(th(hour_totals[h], "text-end", True) for h in hours) + "</TR>")

    return _page(request, "Fish By Time: Month/Hour", "time-report", headers, body)


def fish_of_the(request, d):
    """Fish of the year, of each month and of each week for a chosen year:
    the heaviest WEIGHED fish in each period (same rules as the Home page)."""
    today = localdate()

    # Year selector: the selected angler's years, defaulting to this year
    wanted = request.GET.get("year", "")
    if wanted.isdigit() and int(wanted) in d.years:
        year = int(wanted)
    elif today.year in d.years:
        year = today.year
    else:
        year = d.years[0]

    options = "".join(
        f'<option value="{y}"{" selected" if y == year else ""}>{y}</option>'
        for y in d.years
    )
    year_select = (
        '<label for="id_year" class="ms-3">Year</label>'
        f'<select name="year" id="id_year" onchange="this.form.submit();">{options}</select>'
    )

    weighed = [c for c in d.catches if c.weighed == "Y" and c.trip.date.year == year]

    def heaviest(catches):
        return min(catches, key=lambda c: (-c.weight, c.trip.date, c.catch_time)) if catches else None

    by_month = defaultdict(list)
    by_week = defaultdict(list)
    for c in weighed:
        by_month[c.trip.date.month].append(c)
        by_week[c.trip.date - timedelta(days=c.trip.date.weekday())].append(c)   # Monday

    cols = 6 + (1 if d.all_anglers else 0)

    headers = ("<TR>" + th("Period", "text-start") + th("Fish", "text-start")
               + th("lbs-oz", "text-end")
               + (th("Angler", "text-start") if d.all_anglers else "")
               + th("Venue", "text-start") + th("Date", "text-center")
               + th("Photo", "text-center") + "</TR>\n")

    def row(label, c):
        fish = escape(c.fish.name) if c.fish else ""
        photo = f'<a href="{c.get_absolute_url()}">View</a>' if c.photo == "Y" else ""
        return ("<TR>" + td(label, "text-start")
                + td(f'<a href="{c.get_absolute_url()}">{fish}</a>', "text-start")
                + td(lbs_oz(c.weight), "text-end")
                + (td(escape(angler_name(c.user)), "text-start") if d.all_anglers else "")
                + td(escape(c.trip.venue.name) if c.trip.venue else "", "text-start")
                + td(f'<a href="{c.trip.get_absolute_url()}">{dmy(c.trip.date)}</a>', "text-center")
                + td(photo, "text-center") + "</TR>\n")

    def section(title):
        return f'<TR class="section-row"><TH colspan="{cols}">{title}</TH></TR>\n'

    if not weighed:
        body = f'<TR><TD colspan="{cols}" class="text-center py-3">No weighed fish recorded in {year}.</TD></TR>\n'
    else:
        body = section(f"Fish of the Year &ndash; {year}")
        body += row(str(year), heaviest(weighed))

        body += section("Fish of the Month")
        for m in sorted(by_month):
            body += row(date(year, m, 1).strftime("%B"), heaviest(by_month[m]))

        body += section("Fish of the Week")
        for monday in sorted(by_week):
            body += row("Week starting " + monday.strftime("%-d %b"), heaviest(by_week[monday]))

    return _page(request, "Fish of the &hellip;", "fish-of-report", headers, body,
                 compact=True, extra_filter=year_select)


# Report name in urls.py -> function
REPORTS = {
    "fish_by_species_by_year.html": fish_by_species_by_year,
    "fish_by_venue_by_year.html": fish_by_venue_by_year,
    "fish_by_bait_by_year.html": fish_by_bait_by_year,
    "fish_records.html": fish_records,
    "top_twenty_trips.html": top_twenty_trips,
    "top_twenty_trips_this_year.html": top_twenty_trips_this_year,
    "trip_by_venue_by_year.html": trip_by_venue_by_year,
    "fish_by_time.html": fish_by_time,
    "fish_of_the.html": fish_of_the,
}


TITLES = {
    "fish_by_species_by_year.html": "Fish By Species By Year",
    "fish_by_venue_by_year.html": "Fish By Venue By Year",
    "fish_by_bait_by_year.html": "Fish By Bait By Year",
    "fish_records.html": "Fish Records",
    "top_twenty_trips.html": "Top Twenty Trips",
    "top_twenty_trips_this_year.html": "Top Twenty Trips This Year",
    "trip_by_venue_by_year.html": "Trips By Venue By Year",
    "fish_by_time.html": "Fish By Time: Month/Hour",
    "fish_of_the.html": "Fish of the &hellip;",
}


def render_report(request, report_name):
    report = REPORTS.get(report_name)
    if report is None:
        return mark_safe(
            '<div class="report-card"><h1 class="report-title"><span class="line"></span>'
            'Report unavailable<span class="line"></span></h1>'
            '<p class="text-center">This report does not exist.</p></div>'
        )
    data = Data(selected_angler(request))
    if not data.trips:
        title = TITLES.get(report_name, "Statistics")
        return mark_safe(
            '<div class="report-card">\n'
            f'    <h1 class="report-title"><span class="line"></span>{title}<span class="line"></span></h1>\n'
            + _filter_form(request) +
            '    <p class="text-center text-muted my-4">No trips recorded yet, so there are no statistics to show.</p>\n'
            '</div>\n'
        )
    return mark_safe(report(request, data))
