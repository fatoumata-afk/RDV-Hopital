from rest_framework import serializers

from .models import Department, Room, Specialty


class SpecialtySerializer(serializers.ModelSerializer):
    doctors_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Specialty
        fields = ["id", "name", "slug", "description", "icon", "is_active", "doctors_count"]
        read_only_fields = ["id", "slug"]


class RoomSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Room
        fields = ["id", "code", "name", "department", "department_name", "floor", "is_active"]
        read_only_fields = ["id"]


class DepartmentSerializer(serializers.ModelSerializer):
    location = serializers.CharField(read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "slug",
            "code",
            "description",
            "building",
            "floor",
            "location",
            "phone",
            "is_active",
            "rooms",
        ]
        read_only_fields = ["id", "slug"]
