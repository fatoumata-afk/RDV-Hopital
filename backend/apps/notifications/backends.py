"""Canaux d'envoi. L'architecture reste extensible : un backend e-mail ou SMS
se branche en changeant le réglage ``NOTIFICATION_BACKEND``."""

from django.utils import timezone

from .models import NotificationStatus


class BaseNotificationBackend:
    def send(self, notification):  # pragma: no cover - interface
        raise NotImplementedError


class InAppNotificationBackend(BaseNotificationBackend):
    """Notification consultable dans l'application : rien à transmettre."""

    def send(self, notification):
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at", "updated_at"])
        return notification


class ConsoleNotificationBackend(BaseNotificationBackend):
    """Utile en développement : trace l'envoi dans la console."""

    def send(self, notification):
        print(f"[notification] {notification.recipient.email} : {notification.title}")
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at", "updated_at"])
        return notification
