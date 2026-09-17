"""Rendez-vous et machine à états associée."""

from django.db import models

from apps.common.models import TimeStampedModel


class AppointmentStatus(models.TextChoices):
    BOOKED = "BOOKED", "Réservé"
    CONFIRMED = "CONFIRMED", "Confirmé"
    ARRIVED = "ARRIVED", "Arrivé"
    IN_CONSULTATION = "IN_CONSULTATION", "En consultation"
    COMPLETED = "COMPLETED", "Terminé"
    CANCELLED = "CANCELLED", "Annulé"
    NO_SHOW = "NO_SHOW", "Absent"


#: Transitions autorisées. Tout état terminal (terminé, annulé, absent) est final.
ALLOWED_TRANSITIONS = {
    AppointmentStatus.BOOKED: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.ARRIVED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.ARRIVED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.ARRIVED: {
        AppointmentStatus.IN_CONSULTATION,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.IN_CONSULTATION: {AppointmentStatus.COMPLETED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}

#: États pour lesquels un enregistrement d'arrivée par QR code reste possible.
CHECKIN_ELIGIBLE_STATUSES = {AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED}

#: États considérés comme actifs (rendez-vous à venir non clos).
ACTIVE_STATUSES = {
    AppointmentStatus.BOOKED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.ARRIVED,
    AppointmentStatus.IN_CONSULTATION,
}


class Appointment(TimeStampedModel):
    reference = models.CharField("référence", max_length=20, unique=True)
    patient = models.ForeignKey(
        "accounts.PatientProfile",
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="patient",
    )
    doctor = models.ForeignKey(
        "accounts.DoctorProfile",
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="médecin",
    )
    slot = models.OneToOneField(
        "scheduling.Slot",
        on_delete=models.PROTECT,
        related_name="appointment",
        verbose_name="créneau",
    )
    # Instantané de l'orientation au moment de la réservation.
    specialty = models.ForeignKey(
        "organization.Specialty", on_delete=models.PROTECT, related_name="appointments"
    )
    department = models.ForeignKey(
        "organization.Department", on_delete=models.PROTECT, related_name="appointments"
    )
    room = models.ForeignKey(
        "organization.Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    scheduled_at = models.DateTimeField("date et heure", db_index=True)
    status = models.CharField(
        "statut",
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.BOOKED,
    )
    reason = models.CharField("motif", max_length=255, blank=True)
    cancelled_at = models.DateTimeField("annulé le", null=True, blank=True)
    cancelled_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_appointments",
    )
    cancellation_reason = models.CharField("motif d'annulation", max_length=255, blank=True)

    class Meta:
        verbose_name = "rendez-vous"
        verbose_name_plural = "rendez-vous"
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
            models.Index(fields=["doctor", "scheduled_at"]),
        ]

    def __str__(self):
        return (
            f"{self.reference} · {self.patient.user.full_name} · {self.scheduled_at:%d/%m/%Y %H:%M}"
        )

    @property
    def is_active(self):
        return self.status in ACTIVE_STATUSES

    @property
    def can_check_in(self):
        return self.status in CHECKIN_ELIGIBLE_STATUSES

    @property
    def direction(self):
        """Phrase d'orientation affichée au patient et à l'accueil."""
        parts = [f"{self.specialty.name}", f"Service {self.department.name}"]
        if self.room:
            parts.append(f"Salle {self.room.code}")
        return " — ".join(parts)


class AppointmentStatusHistory(models.Model):
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="status_history"
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "historique de statut"
        verbose_name_plural = "historiques de statut"
        ordering = ["changed_at"]

    def __str__(self):
        return f"{self.appointment_id}: {self.from_status} → {self.to_status}"
