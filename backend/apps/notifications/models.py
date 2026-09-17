from django.db import models

from apps.common.models import TimeStampedModel


class NotificationType(models.TextChoices):
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED", "Confirmation de rendez-vous"
    REMINDER = "REMINDER", "Rappel de rendez-vous"
    CANCELLED = "CANCELLED", "Annulation"
    ARRIVAL_CONFIRMED = "ARRIVAL_CONFIRMED", "Arrivée enregistrée"


class NotificationChannel(models.TextChoices):
    IN_APP = "IN_APP", "Dans l'application"
    EMAIL = "EMAIL", "E-mail"
    SMS = "SMS", "SMS"


class NotificationStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    SENT = "SENT", "Envoyée"
    FAILED = "FAILED", "Échec"


class Notification(TimeStampedModel):
    recipient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notifications"
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    type = models.CharField("type", max_length=30, choices=NotificationType.choices)
    channel = models.CharField(
        "canal",
        max_length=10,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    title = models.CharField("titre", max_length=150)
    message = models.CharField("message", max_length=500)
    status = models.CharField(
        "statut",
        max_length=10,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    read_at = models.DateTimeField("lue le", null=True, blank=True)
    sent_at = models.DateTimeField("envoyée le", null=True, blank=True)

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} → {self.recipient.email}"
