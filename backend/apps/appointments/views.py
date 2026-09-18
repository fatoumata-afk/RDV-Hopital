from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    inline_serializer,
)
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.common.exceptions import BusinessRuleError
from apps.common.permissions import IsAdmin

from .models import ACTIVE_STATUSES, Appointment, AppointmentStatus
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentSerializer,
    CancelAppointmentSerializer,
    DoctorAppointmentSerializer,
    StatusChangeSerializer,
)
from .services import book_appointment, cancel_appointment, transition_status

APPOINTMENT_DETAIL_RESPONSE = PolymorphicProxySerializer(
    component_name="AppointmentDetailResponse",
    serializers=[AppointmentDetailSerializer, DoctorAppointmentSerializer],
    resource_type_field_name=None,
)


class AppointmentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Rendez-vous filtrés selon le rôle : un patient ne voit que les siens,
    un médecin uniquement ceux qui lui sont associés."""

    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "doctor", "specialty", "department"]
    ordering_fields = ["scheduled_at", "created_at"]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, "swagger_fake_view", False):
            return Appointment.objects.none()
        queryset = Appointment.objects.select_related(
            "patient__user", "doctor__user", "specialty", "department", "room", "check_in"
        ).prefetch_related("status_history")
        if user.role == UserRole.PATIENT:
            return queryset.filter(patient__user=user)
        if user.role == UserRole.DOCTOR:
            return queryset.filter(doctor__user=user)
        if user.role == UserRole.ADMIN:
            return queryset
        return queryset.none()

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        if getattr(self.request.user, "role", None) in {UserRole.DOCTOR, UserRole.ADMIN}:
            return DoctorAppointmentSerializer
        if self.action == "retrieve":
            return AppointmentDetailSerializer
        return AppointmentSerializer

    @extend_schema(
        request=AppointmentCreateSerializer, responses={201: AppointmentDetailSerializer}
    )
    def create(self, request, *args, **kwargs):
        if request.user.role != UserRole.PATIENT:
            raise BusinessRuleError(
                "Seul un patient peut réserver un rendez-vous.", status_code=403
            )
        serializer = AppointmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = book_appointment(
            patient=request.user.patient_profile,
            slot_id=serializer.validated_data["slot"],
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(
            AppointmentDetailSerializer(appointment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(responses=AppointmentSerializer(many=True))
    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        queryset = (
            self.get_queryset()
            .filter(scheduled_at__gte=timezone.now(), status__in=ACTIVE_STATUSES)
            .order_by("scheduled_at")
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(responses=AppointmentSerializer(many=True))
    @action(detail=False, methods=["get"])
    def history(self, request):
        queryset = (
            self.get_queryset()
            .filter(
                Q(scheduled_at__lt=timezone.now())
                | Q(
                    status__in=[
                        AppointmentStatus.COMPLETED,
                        AppointmentStatus.CANCELLED,
                        AppointmentStatus.NO_SHOW,
                    ]
                )
            )
            .order_by("-scheduled_at")
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @extend_schema(responses=DoctorAppointmentSerializer(many=True))
    @action(detail=False, methods=["get"])
    def today(self, request):
        today = timezone.localdate()
        queryset = self.get_queryset().filter(scheduled_at__date=today).order_by("scheduled_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def detail_response(self, appointment):
        """Répond avec la même forme que la liste du rôle appelant, pour que le
        frontend puisse remplacer un élément sans perdre de champs."""
        serializer_class = (
            DoctorAppointmentSerializer
            if self.request.user.role in {UserRole.DOCTOR, UserRole.ADMIN}
            else AppointmentDetailSerializer
        )
        return Response(serializer_class(appointment, context={"request": self.request}).data)

    @extend_schema(request=CancelAppointmentSerializer, responses=APPOINTMENT_DETAIL_RESPONSE)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = cancel_appointment(
            appointment=appointment,
            cancelled_by=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )
        return self.detail_response(appointment)

    @extend_schema(request=StatusChangeSerializer, responses=APPOINTMENT_DETAIL_RESPONSE)
    @action(detail=True, methods=["post"], url_path="status")
    def change_status(self, request, pk=None):
        if request.user.role not in {UserRole.DOCTOR, UserRole.ADMIN}:
            raise BusinessRuleError("Action non autorisée.", status_code=403)
        appointment = self.get_object()
        serializer = StatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = transition_status(
            appointment=appointment,
            to_status=serializer.validated_data["status"],
            changed_by=request.user,
            note=serializer.validated_data.get("note", ""),
        )
        return self.detail_response(appointment)


class AdminStatsView(APIView):
    """Statistiques générales pour le tableau de bord administrateur."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses=inline_serializer(
            name="AdminStats",
            fields={
                "patients": serializers.IntegerField(),
                "doctors": serializers.IntegerField(),
                "specialties": serializers.IntegerField(),
                "departments": serializers.IntegerField(),
                "appointments_total": serializers.IntegerField(),
                "appointments_today": serializers.IntegerField(),
                "arrived_today": serializers.IntegerField(),
                "by_status": serializers.DictField(child=serializers.IntegerField()),
                "by_department": serializers.ListField(child=serializers.DictField()),
            },
        )
    )
    def get(self, request):
        from apps.accounts.models import DoctorProfile, PatientProfile
        from apps.checkin.models import CheckIn
        from apps.organization.models import Department, Specialty

        today = timezone.localdate()
        by_status = {
            row["status"]: row["count"]
            for row in Appointment.objects.values("status").annotate(count=Count("id"))
        }
        by_department = list(
            Appointment.objects.values("department__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        return Response(
            {
                "patients": PatientProfile.objects.count(),
                "doctors": DoctorProfile.objects.filter(user__is_active=True).count(),
                "specialties": Specialty.objects.filter(is_active=True).count(),
                "departments": Department.objects.filter(is_active=True).count(),
                "appointments_total": Appointment.objects.count(),
                "appointments_today": Appointment.objects.filter(scheduled_at__date=today).count(),
                # Arrivées réellement enregistrées aujourd'hui, quel que soit le statut atteint
                # ensuite (en consultation, terminé…).
                "arrived_today": CheckIn.objects.filter(arrived_at__date=today).count(),
                "by_status": by_status,
                "by_department": by_department,
            }
        )
