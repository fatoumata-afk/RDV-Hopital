from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import DoctorProfile, UserRole
from apps.common.exceptions import BusinessRuleError

from .models import DoctorSchedule, TimeOff
from .serializers import (
    AvailableDaySerializer,
    DoctorScheduleSerializer,
    SlotSerializer,
    TimeOffSerializer,
)
from .services import apply_time_off, available_days, available_slots, release_time_off


def _parse_date(value, default):
    if not value:
        return default
    from datetime import date

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BusinessRuleError("Format de date invalide (attendu AAAA-MM-JJ).") from exc


class DoctorAvailabilityView(APIView):
    """Dates disposant d'au moins un créneau libre pour un médecin."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("from", str, description="Date de début (AAAA-MM-JJ)"),
            OpenApiParameter("to", str, description="Date de fin (AAAA-MM-JJ)"),
        ],
        responses=AvailableDaySerializer(many=True),
    )
    def get(self, request, doctor_id):
        doctor = get_object_or_404(DoctorProfile.objects.filter(user__is_active=True), pk=doctor_id)
        today = timezone.localdate()
        start = _parse_date(request.query_params.get("from"), today)
        end = _parse_date(request.query_params.get("to"), today + timedelta(days=30))
        start = max(start, today)
        if end < start:
            raise BusinessRuleError("La date de fin précède la date de début.")
        if (end - start).days > 92:
            raise BusinessRuleError("La période demandée ne peut pas dépasser 92 jours.")
        return Response(AvailableDaySerializer(available_days(doctor, start, end), many=True).data)


class DoctorSlotsView(APIView):
    """Créneaux libres d'un médecin pour une date donnée."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter("date", str, required=True)],
        responses=SlotSerializer(many=True),
    )
    def get(self, request, doctor_id):
        doctor = get_object_or_404(DoctorProfile.objects.filter(user__is_active=True), pk=doctor_id)
        day = _parse_date(request.query_params.get("date"), timezone.localdate())
        if day < timezone.localdate():
            return Response([])
        return Response(SlotSerializer(available_slots(doctor, day, day), many=True).data)


class DoctorScheduleViewSet(viewsets.ModelViewSet):
    """Horaires récurrents : un médecin ne gère que les siens, l'admin gère tout."""

    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["doctor", "weekday", "is_active"]

    def get_queryset(self):
        user = self.request.user
        queryset = DoctorSchedule.objects.select_related("doctor__user")
        if user.role == UserRole.ADMIN:
            return queryset
        if user.role == UserRole.DOCTOR:
            return queryset.filter(doctor__user=user)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == UserRole.DOCTOR:
            serializer.save(doctor=user.doctor_profile)
        elif user.role == UserRole.ADMIN:
            if not serializer.validated_data.get("doctor"):
                raise BusinessRuleError("Le médecin est obligatoire.")
            serializer.save()
        else:
            raise BusinessRuleError("Action non autorisée.", status_code=403)


class TimeOffViewSet(viewsets.ModelViewSet):
    serializer_class = TimeOffSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["doctor"]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = TimeOff.objects.select_related("doctor__user")
        if user.role == UserRole.ADMIN:
            return queryset
        if user.role == UserRole.DOCTOR:
            return queryset.filter(doctor__user=user)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == UserRole.DOCTOR:
            time_off = serializer.save(doctor=user.doctor_profile, created_by=user)
        elif user.role == UserRole.ADMIN:
            time_off = serializer.save(created_by=user)
        else:
            raise BusinessRuleError("Action non autorisée.", status_code=403)
        apply_time_off(time_off)

    def perform_destroy(self, instance):
        release_time_off(instance)
        instance.delete()
