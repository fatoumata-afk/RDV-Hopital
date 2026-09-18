from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import IsAdmin

from .models import DoctorProfile, PatientProfile, UserRole
from .serializers import (
    ChangePasswordSerializer,
    CurrentUserSerializer,
    DoctorProfileSerializer,
    LoginSerializer,
    LogoutSerializer,
    PatientProfileSerializer,
    PatientRegistrationSerializer,
    StaffUserCreateSerializer,
    UserSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_scope = "login"


class RegisterView(APIView):
    """Inscription publique réservée aux patients."""

    permission_classes = [AllowAny]
    throttle_scope = "register"

    @extend_schema(request=PatientRegistrationSerializer, responses={201: CurrentUserSerializer})
    def post(self, request):
        serializer = PatientRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        return Response(
            {
                "user": CurrentUserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer, responses={205: None})
    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CurrentUserSerializer)
    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)

    @extend_schema(request=CurrentUserSerializer, responses=CurrentUserSerializer)
    def patch(self, request):
        serializer = CurrentUserSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangePasswordSerializer, responses={204: None})
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """Annuaire des médecins, accessible à tout utilisateur authentifié."""

    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["specialty", "department", "is_accepting_appointments"]
    search_fields = ["user__first_name", "user__last_name", "specialty__name"]

    def get_queryset(self):
        return (
            DoctorProfile.objects.select_related("user", "specialty", "department", "room")
            .filter(user__is_active=True)
            .order_by("user__last_name")
        )


class AdminUserViewSet(viewsets.ModelViewSet):
    """Gestion des comptes par l'administrateur."""

    permission_classes = [IsAdmin]
    serializer_class = UserSerializer
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    queryset = User.objects.all().order_by("last_name", "first_name")

    def get_serializer_class(self):
        if self.action == "create":
            return StaffUserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """Désactivation plutôt que suppression : les rendez-vous restent traçables."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class AdminPatientViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = PatientProfileSerializer
    search_fields = ["user__first_name", "user__last_name", "medical_record_number"]
    queryset = PatientProfile.objects.select_related("user").order_by("user__last_name")


class AdminDoctorViewSet(viewsets.ModelViewSet):
    """Mise à jour de l'affectation des médecins (spécialité, service, salle)."""

    permission_classes = [IsAdmin]
    serializer_class = DoctorProfileSerializer
    queryset = DoctorProfile.objects.select_related(
        "user", "specialty", "department", "room"
    ).order_by("user__last_name")
    http_method_names = ["get", "patch", "put", "head", "options"]


__all__ = [
    "LoginView",
    "RegisterView",
    "LogoutView",
    "CurrentUserView",
    "ChangePasswordView",
    "DoctorViewSet",
    "AdminUserViewSet",
    "AdminPatientViewSet",
    "AdminDoctorViewSet",
    "UserRole",
]
