from datetime import timedelta

import pytest
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentStatus
from apps.appointments.services import book_appointment, cancel_appointment
from apps.checkin.models import CheckIn
from apps.checkin.services import build_payload, confirm_arrival, verify_token
from apps.common.exceptions import BusinessRuleError, ConflictError
from apps.common.test_utils import authenticate

pytestmark = pytest.mark.django_db


@pytest.fixture
def appointment_now(patient, future_slot):
    """Rendez-vous positionné dans la fenêtre d'accueil (dans 10 minutes)."""
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    Appointment.objects.filter(pk=appointment.pk).update(
        scheduled_at=timezone.now() + timedelta(minutes=10)
    )
    appointment.refresh_from_db()
    return appointment


def test_qr_payload_contains_no_personal_data(appointment_now):
    payload = build_payload(appointment_now.token)
    assert payload.startswith("HMS:")
    assert appointment_now.patient.user.last_name.lower() not in payload.lower()
    assert appointment_now.reference not in payload


def test_patient_can_fetch_own_qr_code(api, patient, appointment_now):
    authenticate(api, patient.user.email)
    response = api.get(f"/api/v1/appointments/{appointment_now.id}/qrcode/")
    assert response.status_code == 200
    assert response.data["image"].startswith("data:image/png;base64,")
    assert response.data["payload"].startswith("HMS:")


def test_patient_cannot_fetch_another_patient_qr_code(api, other_patient, appointment_now):
    authenticate(api, other_patient.user.email)
    assert api.get(f"/api/v1/appointments/{appointment_now.id}/qrcode/").status_code == 404


def test_agent_cannot_fetch_qr_code(api, agent, appointment_now):
    authenticate(api, agent.email)
    assert api.get(f"/api/v1/appointments/{appointment_now.id}/qrcode/").status_code == 403


def test_agent_verifies_valid_token(api, agent, appointment_now):
    authenticate(api, agent.email)
    response = api.post(
        "/api/v1/checkin/verify/",
        {"token": build_payload(appointment_now.token)},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["patient_name"] == "Awa Traoré"
    assert response.data["doctor_name"] == "Dr Amadou Diallo"
    assert response.data["room"] == "B-204"
    assert response.data["status"] == AppointmentStatus.BOOKED
    # Aucune donnée médicale ni contact n'est exposé à l'accueil.
    assert "reason" not in response.data
    assert "patient_phone" not in response.data


def test_verify_has_no_side_effect(api, agent, appointment_now):
    authenticate(api, agent.email)
    payload = build_payload(appointment_now.token)
    for _ in range(3):
        assert (
            api.post("/api/v1/checkin/verify/", {"token": payload}, format="json").status_code
            == 200
        )
    appointment_now.refresh_from_db()
    assert appointment_now.status == AppointmentStatus.BOOKED
    assert not CheckIn.objects.exists()


def test_forged_token_is_rejected(api, agent, appointment_now):
    authenticate(api, agent.email)
    forged = f"HMS:{appointment_now.token.token}.0000000000000000"
    response = api.post("/api/v1/checkin/verify/", {"token": forged}, format="json")
    assert response.status_code == 400
    assert response.data["code"] == "token_invalid"


def test_unknown_token_is_rejected(api, agent):
    authenticate(api, agent.email)
    import uuid

    from apps.checkin.services import _sign

    value = str(uuid.uuid4())
    response = api.post(
        "/api/v1/checkin/verify/", {"token": f"HMS:{value}.{_sign(value)}"}, format="json"
    )
    assert response.status_code == 404
    assert response.data["code"] == "token_not_found"


def test_cancelled_appointment_token_is_rejected(admin_user, appointment_now):
    cancel_appointment(appointment=appointment_now, cancelled_by=admin_user)
    appointment_now.refresh_from_db()
    with pytest.raises(BusinessRuleError):
        verify_token(build_payload(appointment_now.token))


def test_token_outside_window_is_rejected(agent, appointment_now):
    Appointment.objects.filter(pk=appointment_now.pk).update(
        scheduled_at=timezone.now() + timedelta(days=2)
    )
    appointment_now.refresh_from_db()
    with pytest.raises(BusinessRuleError) as excinfo:
        verify_token(build_payload(appointment_now.token))
    assert excinfo.value.detail.code == "too_early"


def test_confirm_arrival_records_check_in_and_direction(api, agent, appointment_now):
    authenticate(api, agent.email)
    response = api.post(
        "/api/v1/checkin/confirm/",
        {"token": build_payload(appointment_now.token)},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["direction_note"] == "Cardiologie — Service Cardiologie — Salle B-204"
    assert response.data["appointment"]["status"] == AppointmentStatus.ARRIVED
    appointment_now.refresh_from_db()
    assert appointment_now.status == AppointmentStatus.ARRIVED
    assert appointment_now.token.used_at is not None
    assert appointment_now.notifications.filter(type="ARRIVAL_CONFIRMED").exists()


def test_token_cannot_be_used_twice(api, agent, appointment_now):
    authenticate(api, agent.email)
    payload = build_payload(appointment_now.token)
    assert (
        api.post("/api/v1/checkin/confirm/", {"token": payload}, format="json").status_code == 201
    )
    second = api.post("/api/v1/checkin/confirm/", {"token": payload}, format="json")
    assert second.status_code == 409
    assert second.data["code"] == "already_checked_in"
    assert CheckIn.objects.count() == 1


def test_concurrent_confirmations_create_a_single_check_in(agent, appointment_now):
    payload = build_payload(appointment_now.token)
    confirm_arrival(payload, agent=agent)
    with pytest.raises(ConflictError):
        confirm_arrival(payload, agent=agent)
    assert CheckIn.objects.count() == 1


def test_patient_cannot_validate_arrival(api, patient, appointment_now):
    authenticate(api, patient.user.email)
    response = api.post(
        "/api/v1/checkin/confirm/",
        {"token": build_payload(appointment_now.token)},
        format="json",
    )
    assert response.status_code == 403


def test_doctor_cannot_validate_arrival(api, doctor, appointment_now):
    authenticate(api, doctor.user.email)
    response = api.post(
        "/api/v1/checkin/verify/",
        {"token": build_payload(appointment_now.token)},
        format="json",
    )
    assert response.status_code == 403


def test_manual_code_entry_is_supported(api, agent, appointment_now):
    """Saisie manuelle : le contenu du QR peut être tapé, avec ou sans préfixe."""
    authenticate(api, agent.email)
    raw = build_payload(appointment_now.token).removeprefix("HMS:")
    response = api.post(
        "/api/v1/checkin/confirm/", {"token": raw, "source": "MANUAL"}, format="json"
    )
    assert response.status_code == 201
    assert response.data["source"] == "MANUAL"


def test_recent_check_ins_are_listed_for_agent(api, agent, appointment_now):
    authenticate(api, agent.email)
    api.post(
        "/api/v1/checkin/confirm/",
        {"token": build_payload(appointment_now.token)},
        format="json",
    )
    response = api.get("/api/v1/checkin/recent/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["appointment"]["patient_name"] == "Awa Traoré"
