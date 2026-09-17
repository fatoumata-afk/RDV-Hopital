from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import AgentProfile, DoctorProfile, PatientProfile, User, UserRole
from .services import create_staff_user, register_patient


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "role",
            "is_active",
            "must_change_password",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "date_joined"]


class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = [
            "id",
            "medical_record_number",
            "birth_date",
            "gender",
            "national_id",
            "address",
            "emergency_contact",
        ]
        read_only_fields = ["id", "medical_record_number"]


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Représentation publique d'un médecin (annuaire, réservation)."""

    display_name = serializers.CharField(read_only=True)
    specialty_name = serializers.CharField(source="specialty.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    room_code = serializers.CharField(source="room.code", read_only=True, default=None)

    class Meta:
        model = DoctorProfile
        fields = [
            "id",
            "display_name",
            "specialty",
            "specialty_name",
            "department",
            "department_name",
            "room",
            "room_code",
            "bio",
            "default_slot_duration",
            "is_accepting_appointments",
        ]


class AgentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentProfile
        fields = ["id", "badge_number", "department"]


class CurrentUserSerializer(serializers.ModelSerializer):
    """Utilisateur connecté + son profil métier selon le rôle."""

    full_name = serializers.CharField(read_only=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "role",
            "must_change_password",
            "profile",
        ]
        read_only_fields = ["id", "email", "role", "must_change_password"]

    def get_profile(self, user) -> dict | None:
        if user.is_patient and hasattr(user, "patient_profile"):
            return PatientProfileSerializer(user.patient_profile).data
        if user.is_doctor and hasattr(user, "doctor_profile"):
            return DoctorProfileSerializer(user.doctor_profile).data
        if user.is_agent and hasattr(user, "agent_profile"):
            return AgentProfileSerializer(user.agent_profile).data
        return None

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = self.initial_data.get("profile")
        user = super().update(instance, validated_data)
        if profile_data and user.is_patient and hasattr(user, "patient_profile"):
            profile_serializer = PatientProfileSerializer(
                user.patient_profile, data=profile_data, partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
        return user


class PatientRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(max_length=1, required=False, allow_blank=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return value.lower()

    def create(self, validated_data):
        profile_fields = {
            key: validated_data.pop(key)
            for key in ("birth_date", "gender", "address")
            if key in validated_data
        }
        return register_patient(**validated_data, **profile_fields)


class StaffUserCreateSerializer(serializers.Serializer):
    """Création par un administrateur d'un médecin, agent ou administrateur."""

    role = serializers.ChoiceField(choices=[UserRole.DOCTOR, UserRole.AGENT, UserRole.ADMIN])
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=80)
    last_name = serializers.CharField(max_length=80)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    # Champs médecin
    license_number = serializers.CharField(max_length=40, required=False)
    specialty = serializers.IntegerField(required=False)
    department = serializers.IntegerField(required=False)
    room = serializers.IntegerField(required=False, allow_null=True)
    default_slot_duration = serializers.IntegerField(required=False, min_value=5, max_value=180)
    # Champs agent
    badge_number = serializers.CharField(max_length=30, required=False)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return value.lower()

    def validate(self, attrs):
        role = attrs["role"]
        if role == UserRole.DOCTOR:
            missing = [
                field
                for field in ("license_number", "specialty", "department")
                if not attrs.get(field)
            ]
            if missing:
                raise serializers.ValidationError(
                    {field: "Ce champ est requis pour un médecin." for field in missing}
                )
        if role == UserRole.AGENT and not attrs.get("badge_number"):
            raise serializers.ValidationError(
                {"badge_number": "Ce champ est requis pour un agent d'accueil."}
            )
        return attrs

    def create(self, validated_data):
        role = validated_data["role"]
        doctor_fields = (
            "license_number",
            "specialty",
            "department",
            "room",
            "default_slot_duration",
        )
        agent_fields = ("badge_number", "department")
        allowed = doctor_fields if role == UserRole.DOCTOR else agent_fields
        profile_fields = {}
        for key in set(doctor_fields) | set(agent_fields):
            value = validated_data.pop(key, None)
            if key in allowed and value is not None:
                profile_fields[
                    f"{key}_id" if key in {"specialty", "department", "room"} else key
                ] = value
        return create_staff_user(**validated_data, **profile_fields)


class LogoutSerializer(serializers.Serializer):
    """Jeton de rafraîchissement à révoquer lors de la déconnexion."""

    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """Ajoute le rôle et l'identité au payload de connexion."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = CurrentUserSerializer(self.user).data
        return data
