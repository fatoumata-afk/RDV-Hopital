from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import DoctorProfile

from .models import DoctorSchedule, Slot, TimeOff


class DoctorScheduleSerializer(serializers.ModelSerializer):
    """Le médecin est déduit de l'utilisateur connecté, sauf pour un administrateur."""

    weekday_label = serializers.CharField(source="get_weekday_display", read_only=True)
    valid_from = serializers.DateField(required=False, default=timezone.localdate)
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfile.objects.all(), required=False
    )

    class Meta:
        model = DoctorSchedule
        fields = [
            "id",
            "doctor",
            "weekday",
            "weekday_label",
            "start_time",
            "end_time",
            "slot_duration",
            "valid_from",
            "valid_until",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_time": "L'heure de fin doit être postérieure à l'heure de début."}
            )
        return attrs


class TimeOffSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfile.objects.all(), required=False
    )

    class Meta:
        model = TimeOff
        fields = ["id", "doctor", "start_datetime", "end_datetime", "reason", "created_by"]
        read_only_fields = ["id", "created_by"]

    def validate(self, attrs):
        start = attrs.get("start_datetime", getattr(self.instance, "start_datetime", None))
        end = attrs.get("end_datetime", getattr(self.instance, "end_datetime", None))
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_datetime": "La fin doit être postérieure au début."}
            )
        return attrs


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ["id", "doctor", "date", "start_time", "end_time", "status"]
        read_only_fields = fields


class AvailableDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    slots_count = serializers.IntegerField()
