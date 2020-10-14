from django.shortcuts import render
from django.views import generic
from home.models import Home
from datetime import datetime, timedelta, timezone

#######
#
# index
#
#######
def index(request):
    context = {}
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'home/index.html', context=context)
