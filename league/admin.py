from django.contrib import admin

# Register your models here.

from .models import League, Pl, Ch
admin.site.register(League)
admin.site.register(Pl)
admin.site.register(Ch)
