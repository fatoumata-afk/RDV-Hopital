from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import UserRole
from apps.appointments.models import Appointment
from apps.common.exceptions import BusinessRuleError
from apps.common.permissions import IsAgentOrAdmin

from .models import CheckIn, CheckInSource
from .serializers import (
    AppointmentQrCodeSerializer,
    CheckInAppointmentSerializer,
    CheckInResultSerializer,
    ScanRequestSerializer,
)
from .services import build_payload, confirm_arrival, issue_token, render_qr_data_uri, verify_token


class AppointmentQrCodeView(APIView):
    """QR code d'un rendez-vous, accessible uniquement à son propriétaire."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=AppointmentQrCodeSerializer)
    def get(self, request, pk):
        queryset = Appointment.objects.select_related("token")
        if request.user.role == UserRole.PATIENT:
            queryset = queryset.filter(patient__user=request.user)
        elif request.user.role != UserRole.ADMIN:
            # Ni le médecin ni l'agent n'ont besoin d'accéder au QR d'un patient.
            raise BusinessRuleError("Action non autorisée.", status_code=403)

        appointment = get_object_or_404(queryset, pk=pk)
        token = getattr(appointment, "token", None) or issue_token(appointment)
        if token.is_revoked:
            raise BusinessRuleError(
                "Le QR code de ce rendez-vous n'est plus valide.", code="token_revoked"
            )
        return Response(
            {
                "reference": appointment.reference,
                "payload": build_payload(token),
                "image": render_qr_data_uri(token),
                "expires_at": token.expires_at,
                "is_revoked": token.is_revoked,
            }
        )


class CheckInVerifyView(APIView):
    """Vérifie un QR code sans effet de bord (l'agent peut scanner plusieurs fois)."""

    permission_classes = [IsAgentOrAdmin]
    throttle_scope = "checkin"

    @extend_schema(request=ScanRequestSerializer, responses=CheckInAppointmentSerializer)
    def post(self, request):
        serializer = ScanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, appointment = verify_token(serializer.validated_data["token"])
        return Response(CheckInAppointmentSerializer.from_appointment(appointment).data)


class CheckInConfirmView(APIView):
    """Enregistre l'arrivée du patient et renvoie son orientation."""

    permission_classes = [IsAgentOrAdmin]
    throttle_scope = "checkin"

    @extend_schema(request=ScanRequestSerializer, responses=CheckInResultSerializer)
    def post(self, request):
        serializer = ScanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source = (
            CheckInSource.MANUAL
            if request.data.get("source") == CheckInSource.MANUAL
            else CheckInSource.SCAN
        )
        check_in, _ = confirm_arrival(
            serializer.validated_data["token"], agent=request.user, source=source
        )
        return Response(CheckInResultSerializer(check_in).data, status=status.HTTP_201_CREATED)


class RecentCheckInsView(APIView):
    """Dernières arrivées validées (fil d'activité de l'accueil)."""

    permission_classes = [IsAgentOrAdmin]

    @extend_schema(responses=CheckInResultSerializer(many=True))
    def get(self, request):
        today = timezone.localdate()
        check_ins = (
            CheckIn.objects.select_related(
                "appointment__patient__user",
                "appointment__doctor__user",
                "appointment__specialty",
                "appointment__department",
                "appointment__room",
            )
            .filter(arrived_at__date=today)
            .order_by("-arrived_at")[:20]
        )
        return Response(CheckInResultSerializer(check_ins, many=True).data)
