from datetime import timedelta

import pytest
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentStatus
from apps.appointments.services import book_appointment, cancel_appointment, transition_status
from apps.checkin.models import CheckIn
from apps.common.exceptions import BusinessRuleError, ConflictError
from apps.common.test_utils import authenticate
from apps.scheduling.models import SlotStatus

pytestmark = pytest.mark.django_db


def test_patient_books_a_slot(api, patient, future_slot):
    authenticate(api, patient.user.email)
    response = api.post(
        "/api/v1/appointments/",
        {"slot": future_slot.id, "reason": "Douleurs thoraciques"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == AppointmentStatus.BOOKED
    assert response.data["room_code"] == "B-204"
    assert response.data["direction"].startswith("Cardiologie — Service Cardiologie")
    future_slot.refresh_from_db()
    assert future_slot.status == SlotStatus.BOOKED


def test_booking_generates_qr_token_and_notification(patient, future_slot):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    assert appointment.token is not None
    assert appointment.token.signature
    assert appointment.notifications.filter(type="BOOKING_CONFIRMED").exists()


def test_double_booking_is_rejected(patient, other_patient, future_slot):
    book_appointment(patient=patient, slot_id=future_slot.id)
    with pytest.raises(ConflictError):
        book_appointment(patient=other_patient, slot_id=future_slot.id)
    assert Appointment.objects.count() == 1


def test_concurrent_booking_keeps_a_single_appointment(patient, other_patient, future_slot):
    """Deux réservations quasi simultanées : la seconde doit échouer."""
    results = []
    for booker in (patient, other_patient):
        try:
            results.append(book_appointment(patient=booker, slot_id=future_slot.id))
        except ConflictError:
            results.append(None)
    assert sum(1 for result in results if result is not None) == 1
    assert Appointment.objects.filter(slot=future_slot).count() == 1


def test_booking_a_past_slot_is_rejected(patient, doctor, future_slot):
    future_slot.date = timezone.localdate() - timedelta(days=1)
    future_slot.save(update_fields=["date"])
    with pytest.raises(BusinessRuleError):
        book_appointment(patient=patient, slot_id=future_slot.id)


def test_doctor_cannot_book(api, doctor, future_slot):
    authenticate(api, doctor.user.email)
    response = api.post("/api/v1/appointments/", {"slot": future_slot.id}, format="json")
    assert response.status_code == 403


def test_patient_only_sees_own_appointments(
    api, patient, other_patient, future_slot, doctor, doctor_schedule
):
    from apps.scheduling.services import available_slots

    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    other_slot = [s for s in available_slots(doctor, future_slot.date, future_slot.date)][0]
    other_appointment = book_appointment(patient=other_patient, slot_id=other_slot.id)

    authenticate(api, patient.user.email)
    response = api.get("/api/v1/appointments/")
    assert response.data["count"] == 1
    assert response.data["results"][0]["reference"] == appointment.reference

    # Accès direct par identifiant : le rendez-vous d'autrui reste introuvable.
    assert api.get(f"/api/v1/appointments/{other_appointment.id}/").status_code == 404


def test_doctor_only_sees_own_appointments(api, patient, doctor, other_doctor, future_slot):
    book_appointment(patient=patient, slot_id=future_slot.id)
    authenticate(api, other_doctor.user.email)
    assert api.get("/api/v1/appointments/").data["count"] == 0

    authenticate(api, doctor.user.email)
    response = api.get("/api/v1/appointments/")
    assert response.data["count"] == 1
    assert response.data["results"][0]["patient_name"] == "Awa Traoré"


def test_agent_cannot_list_appointments(api, agent, patient, future_slot):
    book_appointment(patient=patient, slot_id=future_slot.id)
    authenticate(api, agent.email)
    assert api.get("/api/v1/appointments/").data["count"] == 0


def test_patient_can_cancel_before_deadline(api, patient, future_slot):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    authenticate(api, patient.user.email)
    response = api.post(
        f"/api/v1/appointments/{appointment.id}/cancel/",
        {"reason": "Empêchement"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["status"] == AppointmentStatus.CANCELLED
    future_slot.refresh_from_db()
    assert future_slot.status == SlotStatus.AVAILABLE
    appointment.refresh_from_db()
    assert appointment.token.is_revoked is True


def test_patient_cannot_cancel_after_deadline(patient, future_slot):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    Appointment.objects.filter(pk=appointment.pk).update(
        scheduled_at=timezone.now() + timedelta(hours=2)
    )
    appointment.refresh_from_db()
    with pytest.raises(BusinessRuleError):
        cancel_appointment(appointment=appointment, cancelled_by=patient.user)


def test_admin_can_cancel_without_deadline(admin_user, patient, future_slot):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    Appointment.objects.filter(pk=appointment.pk).update(
        scheduled_at=timezone.now() + timedelta(hours=1)
    )
    appointment.refresh_from_db()
    cancelled = cancel_appointment(appointment=appointment, cancelled_by=admin_user)
    assert cancelled.status == AppointmentStatus.CANCELLED


def test_cancelled_appointment_cannot_be_reused(patient, future_slot, admin_user):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    cancel_appointment(appointment=appointment, cancelled_by=patient.user)
    with pytest.raises(ConflictError):
        transition_status(
            appointment=appointment,
            to_status=AppointmentStatus.ARRIVED,
            changed_by=admin_user,
        )


def test_completed_appointment_is_terminal(patient, future_slot, doctor):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    transition_status(
        appointment=appointment, to_status=AppointmentStatus.ARRIVED, changed_by=doctor.user
    )
    transition_status(
        appointment=appointment, to_status=AppointmentStatus.COMPLETED, changed_by=doctor.user
    )
    appointment.refresh_from_db()
    with pytest.raises(ConflictError):
        transition_status(
            appointment=appointment,
            to_status=AppointmentStatus.IN_CONSULTATION,
            changed_by=doctor.user,
        )


def test_patient_cannot_change_status(api, patient, future_slot):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    authenticate(api, patient.user.email)
    response = api.post(
        f"/api/v1/appointments/{appointment.id}/status/",
        {"status": AppointmentStatus.COMPLETED},
        format="json",
    )
    assert response.status_code == 403


def test_doctor_changes_status_of_own_appointment(api, patient, doctor, future_slot):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    authenticate(api, doctor.user.email)
    response = api.post(
        f"/api/v1/appointments/{appointment.id}/status/",
        {"status": AppointmentStatus.CONFIRMED},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["status"] == AppointmentStatus.CONFIRMED
    # Même forme que la liste du médecin : le frontend remplace la ligne sans perdre de champs.
    assert response.data["patient_record_number"] == patient.medical_record_number
    assert response.data["patient_phone"] == patient.user.phone


def test_upcoming_endpoint_returns_next_appointments(api, patient, future_slot):
    book_appointment(patient=patient, slot_id=future_slot.id)
    authenticate(api, patient.user.email)
    response = api.get("/api/v1/appointments/upcoming/")
    assert response.status_code == 200
    assert len(response.data) == 1


def test_admin_stats(api, admin_user, patient, future_slot):
    book_appointment(patient=patient, slot_id=future_slot.id)
    authenticate(api, admin_user.email)
    response = api.get("/api/v1/admin/stats/")
    assert response.status_code == 200
    assert response.data["appointments_total"] == 1
    assert response.data["doctors"] >= 1
    assert response.data["arrived_today"] == 0


def test_admin_stats_count_today_check_ins(api, admin_user, patient, future_slot):
    appointment = book_appointment(patient=patient, slot_id=future_slot.id)
    CheckIn.objects.create(appointment=appointment)
    transition_status(
        appointment=appointment,
        to_status=AppointmentStatus.CONFIRMED,
        changed_by=admin_user,
    )
    authenticate(api, admin_user.email)
    response = api.get("/api/v1/admin/stats/")
    # L'arrivée reste comptée même si le rendez-vous a changé de statut depuis.
    assert response.data["arrived_today"] == 1


def test_stats_are_admin_only(api, patient):
    authenticate(api, patient.user.email)
    assert api.get("/api/v1/admin/stats/").status_code == 403
