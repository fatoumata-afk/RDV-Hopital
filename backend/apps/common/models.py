from django.db import models


class TimeStampedModel(models.Model):
    """Base commune : horodatage de création et de mise à jour."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="modifié le")

    class Meta:
        abstract = True
