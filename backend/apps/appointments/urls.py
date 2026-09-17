from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.checkin.views import AppointmentQrCodeView

from .views import AdminStatsView, AppointmentViewSet

router = DefaultRouter()
router.register("appointments", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path(
        "appointments/<int:pk>/qrcode/",
        AppointmentQrCodeView.as_view(),
        name="appointment-qrcode",
    ),
    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("", include(router.urls)),
]
