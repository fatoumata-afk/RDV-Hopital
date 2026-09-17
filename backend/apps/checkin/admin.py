from django.contrib import admin

from .models import AppointmentToken, CheckIn

admin.site.register([AppointmentToken, CheckIn])
