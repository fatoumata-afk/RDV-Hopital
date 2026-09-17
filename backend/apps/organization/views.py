from django.db.models import Count, Q
from rest_framework import viewsets

from apps.common.permissions import IsAdminOrReadOnly

from .models import Department, Room, Specialty
from .serializers import DepartmentSerializer, RoomSerializer, SpecialtySerializer


class SpecialtyViewSet(viewsets.ModelViewSet):
    serializer_class = SpecialtySerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        queryset = Specialty.objects.annotate(
            doctors_count=Count("doctors", filter=Q(doctors__user__is_active=True))
        ).order_by("name")
        if not (self.request.user.is_authenticated and self.request.user.is_admin_role):
            queryset = queryset.filter(is_active=True)
        return queryset


class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name", "code"]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        queryset = Department.objects.prefetch_related("rooms")
        if not (self.request.user.is_authenticated and self.request.user.is_admin_role):
            queryset = queryset.filter(is_active=True)
        return queryset


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["department", "is_active"]
    search_fields = ["code", "name"]

    def get_queryset(self):
        return Room.objects.select_related("department")
