from django.contrib import admin

from .models import Appointment, AppointmentStatusHistory


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["reference", "patient", "doctor", "scheduled_at", "status"]
    list_filter = ["status", "department", "specialty"]
    search_fields = ["reference", "patient__user__last_name", "doctor__user__last_name"]


admin.site.register(AppointmentStatusHistory)
