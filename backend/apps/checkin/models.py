"""Jeton de rendez-vous (QR code) et enregistrement de l'arrivée."""

import uuid

from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


class AppointmentToken(TimeStampedModel):
    """Jeton opaque encodé dans le QR code.

    Le QR ne contient aucune donnée personnelle : seulement un UUID aléatoire
    et sa signature HMAC, qui permettent au backend de retrouver le rendez-vous.
    """

    appointment = models.OneToOneField(
        "appointments.Appointment", on_delete=models.CASCADE, related_name="token"
    )
    token = models.UUIDField(
        "jeton", default=uuid.uuid4, unique=True, editable=False, db_index=True
    )
    signature = models.CharField("signature", max_length=64)
    issued_at = models.DateTimeField("émis le", auto_now_add=True)
    expires_at = models.DateTimeField("expire le")
    is_revoked = models.BooleanField("révoqué", default=False)
    used_at = models.DateTimeField("utilisé le", null=True, blank=True)

    class Meta:
        verbose_name = "jeton de rendez-vous"
        verbose_name_plural = "jetons de rendez-vous"

    def __str__(self):
        return f"Jeton {self.token} ({self.appointment.reference})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None


class CheckInSource(models.TextChoices):
    SCAN = "SCAN", "Scan du QR code"
    MANUAL = "MANUAL", "Saisie manuelle"


class CheckIn(TimeStampedModel):
    appointment = models.OneToOneField(
        "appointments.Appointment", on_delete=models.CASCADE, related_name="check_in"
    )
    arrived_at = models.DateTimeField("heure d'arrivée", default=timezone.now)
    validated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="validated_check_ins",
        verbose_name="validé par",
    )
    source = models.CharField(
        "origine", max_length=10, choices=CheckInSource.choices, default=CheckInSource.SCAN
    )
    direction_note = models.CharField("orientation", max_length=255, blank=True)

    class Meta:
        verbose_name = "arrivée"
        verbose_name_plural = "arrivées"
        ordering = ["-arrived_at"]

    def __str__(self):
        return f"Arrivée {self.appointment.reference} à {self.arrived_at:%H:%M}"
