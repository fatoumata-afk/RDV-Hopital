"""Logique métier des comptes utilisateurs."""

import secrets

from django.db import transaction
from django.utils import timezone

from .models import AgentProfile, DoctorProfile, PatientProfile, User, UserRole


def generate_medical_record_number():
    """Numéro de dossier lisible et non séquentiel : DOS-<année>-<aléa>."""
    year = timezone.now().year
    while True:
        candidate = f"DOS-{year}-{secrets.randbelow(10**6):06d}"
        if not PatientProfile.objects.filter(medical_record_number=candidate).exists():
            return candidate


@transaction.atomic
def register_patient(*, email, password, first_name, last_name, phone="", **profile_fields):
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=UserRole.PATIENT,
    )
    PatientProfile.objects.create(
        user=user,
        medical_record_number=generate_medical_record_number(),
        **profile_fields,
    )
    return user


@transaction.atomic
def create_staff_user(*, role, email, password, first_name, last_name, phone="", **profile_fields):
    """Création par un administrateur d'un médecin, agent ou administrateur."""
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
    )
    user.must_change_password = True
    if role == UserRole.ADMIN:
        user.is_staff = True
    user.save(update_fields=["must_change_password", "is_staff"])

    if role == UserRole.DOCTOR:
        DoctorProfile.objects.create(user=user, **profile_fields)
    elif role == UserRole.AGENT:
        AgentProfile.objects.create(user=user, **profile_fields)
    return user
