"""Structure de l'hôpital : spécialités, services et salles."""

from django.db import models
from django.utils.text import slugify

from apps.common.models import TimeStampedModel


class Specialty(TimeStampedModel):
    name = models.CharField("nom", max_length=100, unique=True)
    slug = models.SlugField("identifiant", max_length=120, unique=True, blank=True)
    description = models.TextField("description", blank=True)
    icon = models.CharField("icône", max_length=40, blank=True)
    is_active = models.BooleanField("active", default=True)

    class Meta:
        verbose_name = "spécialité"
        verbose_name_plural = "spécialités"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Department(TimeStampedModel):
    """Service hospitalier (ex. Service Cardiologie)."""

    name = models.CharField("nom", max_length=100, unique=True)
    slug = models.SlugField("identifiant", max_length=120, unique=True, blank=True)
    code = models.CharField("code", max_length=10, unique=True)
    description = models.TextField("description", blank=True)
    building = models.CharField("bâtiment", max_length=60, blank=True)
    floor = models.CharField("étage", max_length=30, blank=True)
    phone = models.CharField("téléphone", max_length=30, blank=True)
    is_active = models.BooleanField("actif", default=True)

    class Meta:
        verbose_name = "service"
        verbose_name_plural = "services"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def location(self):
        parts = [p for p in (self.building, self.floor) if p]
        return " · ".join(parts)


class Room(TimeStampedModel):
    """Salle ou zone de consultation rattachée à un service."""

    code = models.CharField("code", max_length=20)
    name = models.CharField("nom", max_length=100, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="rooms", verbose_name="service"
    )
    floor = models.CharField("étage", max_length=30, blank=True)
    is_active = models.BooleanField("active", default=True)

    class Meta:
        verbose_name = "salle"
        verbose_name_plural = "salles"
        ordering = ["department__name", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "code"], name="unique_room_code_per_department"
            )
        ]

    def __str__(self):
        return f"Salle {self.code}"
