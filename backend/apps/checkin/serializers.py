from rest_framework import serializers

from .models import CheckIn


class ScanRequestSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)


class CheckInAppointmentSerializer(serializers.Serializer):
    """Informations strictement nécessaires à l'accueil et à l'orientation.

    Aucun motif de consultation, aucune donnée médicale, aucun contact.
    """

    reference = serializers.CharField()
    patient_name = serializers.CharField()
    doctor_name = serializers.CharField()
    specialty = serializers.CharField()
    department = serializers.CharField()
    department_location = serializers.CharField(allow_blank=True)
    room = serializers.CharField(allow_null=True)
    scheduled_at = serializers.DateTimeField()
    status = serializers.CharField()
    status_label = serializers.CharField()
    direction = serializers.CharField()

    @classmethod
    def from_appointment(cls, appointment):
        return cls(
            {
                "reference": appointment.reference,
                "patient_name": appointment.patient.user.full_name,
                "doctor_name": appointment.doctor.display_name,
                "specialty": appointment.specialty.name,
                "department": appointment.department.name,
                "department_location": appointment.department.location,
                "room": appointment.room.code if appointment.room else None,
                "scheduled_at": appointment.scheduled_at,
                "status": appointment.status,
                "status_label": appointment.get_status_display(),
                "direction": appointment.direction,
            }
        )


class CheckInResultSerializer(serializers.ModelSerializer):
    appointment = serializers.SerializerMethodField()

    class Meta:
        model = CheckIn
        fields = ["id", "arrived_at", "source", "direction_note", "appointment"]

    def get_appointment(self, check_in) -> dict:
        return CheckInAppointmentSerializer.from_appointment(check_in.appointment).data


class AppointmentQrCodeSerializer(serializers.Serializer):
    reference = serializers.CharField()
    payload = serializers.CharField()
    image = serializers.CharField()
    expires_at = serializers.DateTimeField()
    is_revoked = serializers.BooleanField()
