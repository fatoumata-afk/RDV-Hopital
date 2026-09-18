from rest_framework import serializers

from .models import Appointment, AppointmentStatus, AppointmentStatusHistory


class AppointmentStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentStatusHistory
        fields = ["id", "from_status", "to_status", "changed_at", "note"]


class AppointmentSerializer(serializers.ModelSerializer):
    """Vue patient/médecin d'un rendez-vous."""

    doctor_name = serializers.CharField(source="doctor.display_name", read_only=True)
    specialty_name = serializers.CharField(source="specialty.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    room_code = serializers.CharField(source="room.code", read_only=True, default=None)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    direction = serializers.CharField(read_only=True)
    can_cancel = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source="patient.user.full_name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "reference",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "specialty",
            "specialty_name",
            "department",
            "department_name",
            "room",
            "room_code",
            "scheduled_at",
            "status",
            "status_label",
            "direction",
            "reason",
            "can_cancel",
            "cancelled_at",
            "cancellation_reason",
            "created_at",
        ]
        read_only_fields = fields

    def get_can_cancel(self, appointment) -> bool:
        from .services import can_patient_cancel

        if appointment.status not in {AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED}:
            return False
        request = self.context.get("request")
        if request and request.user.is_patient:
            return can_patient_cancel(appointment)
        return True


class AppointmentDetailSerializer(AppointmentSerializer):
    status_history = AppointmentStatusHistorySerializer(many=True, read_only=True)
    department_location = serializers.CharField(source="department.location", read_only=True)
    arrived_at = serializers.DateTimeField(
        source="check_in.arrived_at", read_only=True, default=None
    )

    class Meta(AppointmentSerializer.Meta):
        fields = AppointmentSerializer.Meta.fields + [
            "status_history",
            "department_location",
            "arrived_at",
        ]
        read_only_fields = fields


class DoctorAppointmentSerializer(AppointmentSerializer):
    """Vue médecin : ajoute les informations patient nécessaires à la consultation."""

    patient_record_number = serializers.CharField(
        source="patient.medical_record_number", read_only=True
    )
    patient_birth_date = serializers.DateField(source="patient.birth_date", read_only=True)
    patient_phone = serializers.CharField(source="patient.user.phone", read_only=True)
    arrived_at = serializers.DateTimeField(
        source="check_in.arrived_at", read_only=True, default=None
    )

    class Meta(AppointmentSerializer.Meta):
        fields = AppointmentSerializer.Meta.fields + [
            "patient_record_number",
            "patient_birth_date",
            "patient_phone",
            "arrived_at",
        ]
        read_only_fields = fields


class AppointmentCreateSerializer(serializers.Serializer):
    slot = serializers.IntegerField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class CancelAppointmentSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class StatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=AppointmentStatus.choices)
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)
