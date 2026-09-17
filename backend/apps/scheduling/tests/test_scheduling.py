from datetime import date, time, timedelta

import pytest
from django.utils import timezone

from apps.common.test_utils import authenticate
from apps.scheduling.models import Slot
from apps.scheduling.services import available_slots, generate_slots

pytestmark = pytest.mark.django_db


def test_slots_follow_doctor_schedule(doctor, doctor_schedule):
    day = timezone.localdate() + timedelta(days=2)
    slots = available_slots(doctor, day, day)
    # 8h → 18h par pas de 30 min = 20 créneaux
    assert len(slots) == 20
    assert slots[0].start_time == time(8, 0)
    assert slots[-1].end_time == time(18, 0)


def test_generation_is_idempotent(doctor, doctor_schedule):
    day = timezone.localdate() + timedelta(days=2)
    generate_slots(doctor, day, day)
    count = Slot.objects.filter(doctor=doctor, date=day).count()
    generate_slots(doctor, day, day)
    assert Slot.objects.filter(doctor=doctor, date=day).count() == count


def test_past_slots_are_never_generated(doctor, doctor_schedule):
    yesterday = timezone.localdate() - timedelta(days=1)
    assert generate_slots(doctor, yesterday, yesterday) == []


def test_time_off_blocks_slots(api, doctor, doctor_schedule):
    day = timezone.localdate() + timedelta(days=2)
    available_slots(doctor, day, day)
    authenticate(api, doctor.user.email)
    response = api.post(
        "/api/v1/time-off/",
        {
            "start_datetime": f"{day.isoformat()}T00:00:00Z",
            "end_datetime": f"{day.isoformat()}T23:59:00Z",
            "reason": "Congé",
        },
        format="json",
    )
    assert response.status_code == 201
    assert available_slots(doctor, day, day) == []


def test_doctor_only_sees_own_schedules(api, doctor, other_doctor, doctor_schedule):
    authenticate(api, other_doctor.user.email)
    response = api.get("/api/v1/schedules/")
    assert response.status_code == 200
    assert response.data["count"] == 0


def test_doctor_cannot_create_schedule_for_another_doctor(api, doctor, other_doctor):
    authenticate(api, other_doctor.user.email)
    response = api.post(
        "/api/v1/schedules/",
        {
            "doctor": doctor.id,
            "weekday": 1,
            "start_time": "09:00",
            "end_time": "12:00",
            "slot_duration": 30,
            "valid_from": date.today().isoformat(),
        },
        format="json",
    )
    assert response.status_code == 201
    # Le médecin est forcé à l'utilisateur connecté, jamais celui envoyé par le client.
    assert response.data["doctor"] == other_doctor.id


def test_schedule_rejects_inverted_hours(api, doctor):
    authenticate(api, doctor.user.email)
    response = api.post(
        "/api/v1/schedules/",
        {
            "weekday": 1,
            "start_time": "15:00",
            "end_time": "09:00",
            "slot_duration": 30,
            "valid_from": date.today().isoformat(),
        },
        format="json",
    )
    assert response.status_code == 400


def test_availability_endpoint_lists_days_with_free_slots(api, patient, doctor, doctor_schedule):
    authenticate(api, patient.user.email)
    start = timezone.localdate() + timedelta(days=1)
    response = api.get(
        f"/api/v1/doctors/{doctor.id}/availability/?from={start}&to={start + timedelta(days=3)}"
    )
    assert response.status_code == 200
    assert len(response.data) == 4
    assert response.data[0]["slots_count"] == 20


def test_agent_cannot_manage_schedules(api, agent, doctor_schedule):
    authenticate(api, agent.email)
    assert api.get("/api/v1/schedules/").data["count"] == 0
