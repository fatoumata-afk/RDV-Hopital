from django.contrib import admin

from .models import DoctorSchedule, Slot, TimeOff

admin.site.register([DoctorSchedule, TimeOff, Slot])
