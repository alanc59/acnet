from django.contrib import admin

# Register your models here.

from .models import League, Pl, Ch, Td
admin.site.register(League)
admin.site.register(Pl)
admin.site.register(Ch)
admin.site.register(Td)
