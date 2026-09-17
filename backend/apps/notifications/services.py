"""Construction et envoi des notifications liées au parcours patient."""

from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string

from .models import Notification, NotificationType


def _backend():
    return import_string(settings.NOTIFICATION_BACKEND)()


def _content(appointment, notification_type):
    when = timezone.localtime(appointment.scheduled_at)
    templates = {
        NotificationType.BOOKING_CONFIRMED: (
            "Rendez-vous confirmé",
            f"Votre rendez-vous avec {appointment.doctor.display_name} est confirmé "
            f"le {when:%d/%m/%Y} à {when:%H:%M}. {appointment.direction}.",
        ),
        NotificationType.REMINDER: (
            "Rappel de rendez-vous",
            f"Rappel : rendez-vous avec {appointment.doctor.display_name} "
            f"le {when:%d/%m/%Y} à {when:%H:%M}.",
        ),
        NotificationType.CANCELLED: (
            "Rendez-vous annulé",
            f"Votre rendez-vous du {when:%d/%m/%Y} à {when:%H:%M} a été annulé.",
        ),
        NotificationType.ARRIVAL_CONFIRMED: (
            "Arrivée enregistrée",
            f"Votre arrivée est enregistrée. Orientation : {appointment.direction}.",
        ),
    }
    return templates[notification_type]


def notify(appointment, notification_type):
    """Crée et envoie une notification au patient du rendez-vous."""
    notification_type = NotificationType(notification_type)
    title, message = _content(appointment, notification_type)
    notification = Notification.objects.create(
        recipient=appointment.patient.user,
        appointment=appointment,
        type=notification_type,
        title=title,
        message=message,
    )
    return _backend().send(notification)
