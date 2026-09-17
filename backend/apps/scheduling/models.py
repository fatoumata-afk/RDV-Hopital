"""Horaires des médecins, blocages et créneaux de consultation."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Lundi"
    TUESDAY = 1, "Mardi"
    WEDNESDAY = 2, "Mercredi"
    THURSDAY = 3, "Jeudi"
    FRIDAY = 4, "Vendredi"
    SATURDAY = 5, "Samedi"
    SUNDAY = 6, "Dimanche"


class DoctorSchedule(TimeStampedModel):
    """Plage horaire récurrente hebdomadaire d'un médecin."""

    doctor = models.ForeignKey(
        "accounts.DoctorProfile",
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="médecin",
    )
    weekday = models.IntegerField("jour", choices=Weekday.choices)
    start_time = models.TimeField("heure de début")
    end_time = models.TimeField("heure de fin")
    slot_duration = models.PositiveSmallIntegerField("durée du créneau (min)", default=30)
    valid_from = models.DateField("valable à partir du")
    valid_until = models.DateField("valable jusqu'au", null=True, blank=True)
    is_active = models.BooleanField("active", default=True)

    class Meta:
        verbose_name = "horaire"
        verbose_name_plural = "horaires"
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_time__lt=models.F("end_time")),
                name="schedule_start_before_end",
            )
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("L'heure de début doit précéder l'heure de fin.")
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError("La date de fin de validité précède la date de début.")

    def __str__(self):
        return (
            f"{self.doctor} · {self.get_weekday_display()} "
            f"{self.start_time:%H:%M}-{self.end_time:%H:%M}"
        )

    def covers(self, day):
        if not self.is_active or day.weekday() != self.weekday:
            return False
        if day < self.valid_from:
            return False
        return self.valid_until is None or day <= self.valid_until


class TimeOff(TimeStampedModel):
    """Absence ou plage bloquée par le médecin (ou par un administrateur)."""

    doctor = models.ForeignKey(
        "accounts.DoctorProfile",
        on_delete=models.CASCADE,
        related_name="time_off",
        verbose_name="médecin",
    )
    start_datetime = models.DateTimeField("début")
    end_datetime = models.DateTimeField("fin")
    reason = models.CharField("motif", max_length=200, blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_time_off",
    )

    class Meta:
        verbose_name = "indisponibilité"
        verbose_name_plural = "indisponibilités"
        ordering = ["-start_datetime"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_datetime__lt=models.F("end_datetime")),
                name="timeoff_start_before_end",
            )
        ]

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("Le début doit précéder la fin.")

    def __str__(self):
        return f"{self.doctor} indisponible du {self.start_datetime} au {self.end_datetime}"


class SlotStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Disponible"
    BOOKED = "BOOKED", "Réservé"
    BLOCKED = "BLOCKED", "Bloqué"


class Slot(TimeStampedModel):
    """Créneau unitaire. L'unicité (médecin, date, heure) garantit qu'un médecin
    ne peut jamais avoir deux rendez-vous au même moment."""

    doctor = models.ForeignKey(
        "accounts.DoctorProfile",
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name="médecin",
    )
    date = models.DateField("date")
    start_time = models.TimeField("heure de début")
    end_time = models.TimeField("heure de fin")
    status = models.CharField(
        "statut", max_length=10, choices=SlotStatus.choices, default=SlotStatus.AVAILABLE
    )
    generated_from = models.ForeignKey(
        DoctorSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="slots",
    )

    class Meta:
        verbose_name = "créneau"
        verbose_name_plural = "créneaux"
        ordering = ["date", "start_time"]
        indexes = [models.Index(fields=["doctor", "date", "status"])]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "start_time"], name="unique_slot_per_doctor"
            )
        ]

    def __str__(self):
        return f"{self.doctor} · {self.date} {self.start_time:%H:%M}"

    @property
    def is_available(self):
        return self.status == SlotStatus.AVAILABLE
