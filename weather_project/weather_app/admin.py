from django.contrib import admin
from .models import Location

class LocationAdmin(admin.ModelAdmin):
    # Display read-only fields in admin interface
    readonly_fields = ('date_last_showed', 'id')

# Register your models here.
admin.site.register(Location, LocationAdmin)
