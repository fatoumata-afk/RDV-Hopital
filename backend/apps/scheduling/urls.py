from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DoctorAvailabilityView,
    DoctorScheduleViewSet,
    DoctorSlotsView,
    TimeOffViewSet,
)

router = DefaultRouter()
router.register("schedules", DoctorScheduleViewSet, basename="schedule")
router.register("time-off", TimeOffViewSet, basename="time-off")

urlpatterns = [
    path(
        "doctors/<int:doctor_id>/availability/",
        DoctorAvailabilityView.as_view(),
        name="doctor-availability",
    ),
    path("doctors/<int:doctor_id>/slots/", DoctorSlotsView.as_view(), name="doctor-slots"),
    path("", include(router.urls)),
]
