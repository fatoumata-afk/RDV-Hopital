"""Émission, vérification et consommation des QR codes de rendez-vous.

Format du contenu du QR : ``HMS:<uuid>.<signature>``.
La signature est un HMAC-SHA256 tronqué calculé avec la SECRET_KEY du serveur,
ce qui rend le jeton infalsifiable sans exposer la moindre donnée personnelle.
"""

import base64
import hashlib
import hmac
import io
from datetime import timedelta

import qrcode
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentStatus
from apps.common.exceptions import BusinessRuleError, ConflictError

from .models import AppointmentToken, CheckIn, CheckInSource

TOKEN_PREFIX = "HMS"
SIGNATURE_LENGTH = 16


def _sign(token_value):
    digest = hmac.new(
        settings.SECRET_KEY.encode(), str(token_value).encode(), hashlib.sha256
    ).hexdigest()
    return digest[:SIGNATURE_LENGTH]


def build_payload(token):
    return f"{TOKEN_PREFIX}:{token.token}.{token.signature}"


def parse_payload(payload):
    """Extrait et vérifie l'UUID signé d'un contenu de QR code."""
    if not payload or not isinstance(payload, str):
        raise BusinessRuleError("Code invalide.", code="token_invalid", status_code=400)
    raw = payload.strip()
    if raw.startswith(f"{TOKEN_PREFIX}:"):
        raw = raw[len(TOKEN_PREFIX) + 1 :]
    if "." not in raw:
        raise BusinessRuleError("Code invalide.", code="token_invalid", status_code=400)
    token_value, signature = raw.rsplit(".", 1)
    if not hmac.compare_digest(_sign(token_value), signature.lower()):
        raise BusinessRuleError("Code invalide.", code="token_invalid", status_code=400)
    return token_value


def issue_token(appointment):
    """Crée le jeton du rendez-vous (appelé automatiquement à la réservation)."""
    token = AppointmentToken(
        appointment=appointment,
        expires_at=appointment.scheduled_at + timedelta(hours=12),
    )
    token.signature = _sign(token.token)
    token.save()
    return token


def revoke_token(appointment):
    AppointmentToken.objects.filter(appointment=appointment, is_revoked=False).update(
        is_revoked=True
    )


def render_qr_png(token):
    """Image PNG du QR code, générée à la demande (jamais stockée)."""
    image = qrcode.make(build_payload(token), box_size=10, border=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def render_qr_data_uri(token):
    return "data:image/png;base64," + base64.b64encode(render_qr_png(token)).decode()


def _load_token(payload):
    token_value = parse_payload(payload)
    try:
        return AppointmentToken.objects.select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
            "appointment__specialty",
            "appointment__department",
            "appointment__room",
        ).get(token=token_value)
    except (AppointmentToken.DoesNotExist, ValueError) as exc:
        raise BusinessRuleError(
            "Aucun rendez-vous ne correspond à ce code.",
            code="token_not_found",
            status_code=404,
        ) from exc


def verify_token(payload, *, now=None):
    """Vérifie un QR code sans aucun effet de bord et renvoie le rendez-vous."""
    now = now or timezone.now()
    token = _load_token(payload)
    appointment = token.appointment

    if token.is_revoked:
        raise BusinessRuleError("Ce code a été révoqué.", code="token_revoked")
    if token.is_expired:
        raise BusinessRuleError("Ce code a expiré.", code="token_expired")
    if appointment.status == AppointmentStatus.CANCELLED:
        raise BusinessRuleError("Ce rendez-vous a été annulé.", code="appointment_cancelled")
    if appointment.status in {AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW}:
        raise BusinessRuleError("Ce rendez-vous n'est plus actif.", code="appointment_closed")
    if hasattr(appointment, "check_in"):
        raise ConflictError(
            "L'arrivée de ce patient a déjà été enregistrée à "
            f"{timezone.localtime(appointment.check_in.arrived_at):%H:%M}.",
            code="already_checked_in",
        )
    if not appointment.can_check_in:
        raise ConflictError(
            "Ce rendez-vous ne peut pas être enregistré à l'accueil.",
            code="invalid_status",
        )

    window_start = appointment.scheduled_at - timedelta(
        minutes=settings.CHECKIN_WINDOW_BEFORE_MINUTES
    )
    window_end = appointment.scheduled_at + timedelta(minutes=settings.CHECKIN_WINDOW_AFTER_MINUTES)
    if now < window_start:
        raise BusinessRuleError(
            "Ce rendez-vous n'est pas encore ouvert à l'accueil "
            f"(à partir du {timezone.localtime(window_start):%d/%m/%Y %H:%M}).",
            code="too_early",
        )
    if now > window_end:
        raise BusinessRuleError(
            "La fenêtre d'enregistrement de ce rendez-vous est dépassée.",
            code="too_late",
        )
    return token, appointment


@transaction.atomic
def confirm_arrival(payload, *, agent, source=CheckInSource.SCAN):
    """Enregistre l'arrivée du patient après re-vérification complète du jeton."""
    token, appointment = verify_token(payload)
    # Verrou : empêche deux validations concurrentes de créer deux arrivées.
    appointment = (
        Appointment.objects.select_for_update()
        .select_related("patient__user", "doctor__user", "specialty", "department", "room")
        .get(pk=appointment.pk)
    )
    if CheckIn.objects.filter(appointment=appointment).exists():
        raise ConflictError("Arrivée déjà enregistrée.", code="already_checked_in")

    from apps.appointments.services import transition_status

    check_in = CheckIn.objects.create(
        appointment=appointment,
        arrived_at=timezone.now(),
        validated_by=agent,
        source=source,
        direction_note=appointment.direction,
    )
    transition_status(
        appointment=appointment,
        to_status=AppointmentStatus.ARRIVED,
        changed_by=agent,
        note="Arrivée validée à l'accueil",
    )
    appointment.refresh_from_db()
    token.used_at = timezone.now()
    token.save(update_fields=["used_at", "updated_at"])

    from apps.notifications.services import notify

    notify(appointment, "ARRIVAL_CONFIRMED")
    return check_in, appointment
