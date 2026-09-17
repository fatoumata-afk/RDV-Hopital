from django.urls import path

from .views import CheckInConfirmView, CheckInVerifyView, RecentCheckInsView

urlpatterns = [
    path("verify/", CheckInVerifyView.as_view(), name="checkin-verify"),
    path("confirm/", CheckInConfirmView.as_view(), name="checkin-confirm"),
    path("recent/", RecentCheckInsView.as_view(), name="checkin-recent"),
]
