from django.contrib import admin

# Register your models here.

from .models import Bait, Catch, Fish, Trip, Venue
admin.site.register(Bait)
admin.site.register(Catch)
admin.site.register(Fish)
admin.site.register(Trip)
admin.site.register(Venue)
