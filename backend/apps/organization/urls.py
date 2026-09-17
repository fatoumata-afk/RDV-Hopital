from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    AdminDoctorViewSet,
    AdminPatientViewSet,
    AdminUserViewSet,
    DoctorViewSet,
)

from .views import DepartmentViewSet, RoomViewSet, SpecialtyViewSet

router = DefaultRouter()
router.register("specialties", SpecialtyViewSet, basename="specialty")
router.register("departments", DepartmentViewSet, basename="department")
router.register("rooms", RoomViewSet, basename="room")
router.register("doctors", DoctorViewSet, basename="doctor")
router.register("admin/users", AdminUserViewSet, basename="admin-user")
router.register("admin/patients", AdminPatientViewSet, basename="admin-patient")
router.register("admin/doctors", AdminDoctorViewSet, basename="admin-doctor")

urlpatterns = [path("", include(router.urls))]
