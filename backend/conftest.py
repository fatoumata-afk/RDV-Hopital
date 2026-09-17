"""Fixtures partagées par les tests."""

from datetime import time, timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.accounts.services import create_staff_user, register_patient
from apps.common.test_utils import PASSWORD
from apps.organization.models import Department, Room, Specialty
from apps.scheduling.models import DoctorSchedule
from apps.scheduling.services import available_slots


@pytest.fixture(autouse=True)
def reset_throttling():
    """Le throttling est réel en test : on repart d'un compteur vide."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def specialty(db):
    return Specialty.objects.create(name="Cardiologie")


@pytest.fixture
def department(db):
    return Department.objects.create(name="Cardiologie", code="CARD", building="Bâtiment B")


@pytest.fixture
def room(department):
    return Room.objects.create(code="B-204", department=department)


@pytest.fixture
def doctor(specialty, department, room):
    user = create_staff_user(
        role=UserRole.DOCTOR,
        email="dr.diallo@test.local",
        password=PASSWORD,
        first_name="Amadou",
        last_name="Diallo",
        license_number="ORD-1",
        specialty_id=specialty.id,
        department_id=department.id,
        room_id=room.id,
    )
    return user.doctor_profile


@pytest.fixture
def other_doctor(specialty, department):
    user = create_staff_user(
        role=UserRole.DOCTOR,
        email="dr.bah@test.local",
        password=PASSWORD,
        first_name="Fatoumata",
        last_name="Bah",
        license_number="ORD-2",
        specialty_id=specialty.id,
        department_id=department.id,
    )
    return user.doctor_profile


@pytest.fixture
def patient(db):
    return register_patient(
        email="awa@test.local",
        password=PASSWORD,
        first_name="Awa",
        last_name="Traoré",
    ).patient_profile


@pytest.fixture
def other_patient(db):
    return register_patient(
        email="moussa@test.local",
        password=PASSWORD,
        first_name="Moussa",
        last_name="Konaté",
    ).patient_profile


@pytest.fixture
def agent(db, department):
    return create_staff_user(
        role=UserRole.AGENT,
        email="accueil@test.local",
        password=PASSWORD,
        first_name="Salif",
        last_name="Accueil",
        badge_number="AG-1",
        department_id=department.id,
    )


@pytest.fixture
def admin_user(db):
    return create_staff_user(
        role=UserRole.ADMIN,
        email="admin@test.local",
        password=PASSWORD,
        first_name="Awa",
        last_name="Admin",
    )


@pytest.fixture
def doctor_schedule(doctor):
    """Horaires actifs tous les jours, pour disposer de créneaux futurs."""
    today = timezone.localdate()
    schedules = []
    for weekday in range(7):
        schedules.append(
            DoctorSchedule.objects.create(
                doctor=doctor,
                weekday=weekday,
                start_time=time(8, 0),
                end_time=time(18, 0),
                slot_duration=30,
                valid_from=today - timedelta(days=1),
            )
        )
    return schedules


@pytest.fixture
def future_slot(doctor, doctor_schedule):
    """Premier créneau libre à au moins 48 h, pour pouvoir tester l'annulation."""
    start = timezone.localdate() + timedelta(days=3)
    slots = available_slots(doctor, start, start + timedelta(days=1))
    assert slots, "Aucun créneau généré"
    return slots[0]
