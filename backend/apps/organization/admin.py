from django.contrib import admin

from .models import Department, Room, Specialty

admin.site.register([Specialty, Department, Room])
