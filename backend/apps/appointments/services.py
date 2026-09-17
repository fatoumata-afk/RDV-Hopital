"""Règles métier des rendez-vous : réservation, transitions, annulation."""

import secrets
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import BusinessRuleError, ConflictError
from apps.scheduling.models import Slot, SlotStatus

from .models import (
    ALLOWED_TRANSITIONS,
    Appointment,
    AppointmentStatus,
    AppointmentStatusHistory,
)


def generate_reference():
    year = timezone.now().year
    while True:
        candidate = f"RDV-{year}-{secrets.randbelow(10**6):06d}"
        if not Appointment.objects.filter(reference=candidate).exists():
            return candidate


def slot_datetime(slot):
    return timezone.make_aware(
        datetime.combine(slot.date, slot.start_time), timezone.get_current_timezone()
    )


@transaction.atomic
def book_appointment(*, patient, slot_id, reason=""):
    """Réserve un créneau de façon atomique.

    Le verrou `select_for_update` sur le créneau empêche deux patients de
    réserver le même créneau simultanément : le second obtient un 409.
    """
    try:
        slot = (
            Slot.objects.select_for_update()
            .select_related(
                "doctor__user", "doctor__specialty", "doctor__department", "doctor__room"
            )
            .get(pk=slot_id)
        )
    except Slot.DoesNotExist as exc:
        raise BusinessRuleError(
            "Créneau introuvable.", code="slot_not_found", status_code=404
        ) from exc

    if slot.status != SlotStatus.AVAILABLE:
        raise ConflictError("Ce créneau n'est plus disponible.", code="slot_unavailable")

    scheduled_at = slot_datetime(slot)
    if scheduled_at <= timezone.now():
        raise BusinessRuleError("Ce créneau est déjà passé.", code="slot_in_past")

    doctor = slot.doctor
    if not doctor.is_accepting_appointments:
        raise BusinessRuleError(
            "Ce médecin n'accepte pas de nouveaux rendez-vous.", code="doctor_unavailable"
        )

    conflicting = Appointment.objects.filter(
        patient=patient,
        scheduled_at=scheduled_at,
        status__in=[AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED],
    ).exists()
    if conflicting:
        raise ConflictError(
            "Vous avez déjà un rendez-vous à cet horaire.", code="patient_double_booking"
        )

    slot.status = SlotStatus.BOOKED
    slot.save(update_fields=["status", "updated_at"])

    appointment = Appointment.objects.create(
        reference=generate_reference(),
        patient=patient,
        doctor=doctor,
        slot=slot,
        specialty=doctor.specialty,
        department=doctor.department,
        room=doctor.room,
        scheduled_at=scheduled_at,
        status=AppointmentStatus.BOOKED,
        reason=reason,
    )
    AppointmentStatusHistory.objects.create(
        appointment=appointment,
        from_status="",
        to_status=AppointmentStatus.BOOKED,
        changed_by=patient.user,
        note="Réservation en ligne",
    )

    # Import local : évite un cycle d'import entre applications.
    from apps.checkin.services import issue_token
    from apps.notifications.services import notify

    issue_token(appointment)
    notify(appointment, "BOOKING_CONFIRMED")
    return appointment


def can_patient_cancel(appointment, now=None):
    now = now or timezone.now()
    deadline_hours = settings.APPOINTMENT_CANCELLATION_DEADLINE_HOURS
    remaining = (appointment.scheduled_at - now).total_seconds() / 3600
    return remaining >= deadline_hours


@transaction.atomic
def cancel_appointment(*, appointment, cancelled_by, reason=""):
    appointment = (
        Appointment.objects.select_for_update().select_related("slot").get(pk=appointment.pk)
    )
    if appointment.status == AppointmentStatus.CANCELLED:
        raise ConflictError("Ce rendez-vous est déjà annulé.", code="already_cancelled")
    if AppointmentStatus.CANCELLED not in ALLOWED_TRANSITIONS[appointment.status]:
        raise ConflictError(
            "Ce rendez-vous ne peut plus être annulé.", code="cancellation_not_allowed"
        )
    if cancelled_by.is_patient and not can_patient_cancel(appointment):
        raise BusinessRuleError(
            "L'annulation doit intervenir au moins "
            f"{settings.APPOINTMENT_CANCELLATION_DEADLINE_HOURS} h avant le rendez-vous.",
            code="cancellation_deadline_passed",
        )

    previous = appointment.status
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = timezone.now()
    appointment.cancelled_by = cancelled_by
    appointment.cancellation_reason = reason
    appointment.save(
        update_fields=[
            "status",
            "cancelled_at",
            "cancelled_by",
            "cancellation_reason",
            "updated_at",
        ]
    )

    slot = appointment.slot
    if slot_datetime(slot) > timezone.now():
        slot.status = SlotStatus.AVAILABLE
        slot.save(update_fields=["status", "updated_at"])

    AppointmentStatusHistory.objects.create(
        appointment=appointment,
        from_status=previous,
        to_status=AppointmentStatus.CANCELLED,
        changed_by=cancelled_by,
        note=reason,
    )

    from apps.checkin.services import revoke_token
    from apps.notifications.services import notify

    revoke_token(appointment)
    notify(appointment, "CANCELLED")
    return appointment


@transaction.atomic
def transition_status(*, appointment, to_status, changed_by, note=""):
    """Applique une transition de statut si elle est autorisée."""
    appointment = Appointment.objects.select_for_update().get(pk=appointment.pk)
    current = AppointmentStatus(appointment.status)
    target = AppointmentStatus(to_status)
    if target == current:
        return appointment
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ConflictError(
            f"Transition impossible : {current.label} → {target.label}.",
            code="invalid_transition",
        )

    appointment.status = target
    appointment.save(update_fields=["status", "updated_at"])
    AppointmentStatusHistory.objects.create(
        appointment=appointment,
        from_status=current,
        to_status=target,
        changed_by=changed_by,
        note=note,
    )
    return appointment
