from django.shortcuts import render
from django.views import generic
from league.models import League, Pl, Ch, Td

def index(request):
    """View function for home page of site."""

    context = {}

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'league/index.html', context=context)

class PLListView(generic.ListView):
    model = Pl

class CHListView(generic.ListView):
    model = Ch

class TDListView(generic.ListView):
    model = Td
