import pytest

from apps.common.test_utils import authenticate

pytestmark = pytest.mark.django_db


def test_catalog_requires_authentication(api):
    assert api.get("/api/v1/specialties/").status_code == 401


def test_patient_can_read_but_not_write_catalog(api, patient, specialty):
    authenticate(api, patient.user.email)
    response = api.get("/api/v1/specialties/")
    assert response.status_code == 200
    assert response.data["results"][0]["name"] == "Cardiologie"
    assert (
        api.post("/api/v1/specialties/", {"name": "Pneumologie"}, format="json").status_code == 403
    )


def test_admin_manages_specialties_departments_and_rooms(api, admin_user, department):
    authenticate(api, admin_user.email)
    specialty = api.post("/api/v1/specialties/", {"name": "Pneumologie"}, format="json")
    assert specialty.status_code == 201
    assert specialty.data["slug"] == "pneumologie"

    room = api.post("/api/v1/rooms/", {"code": "B-999", "department": department.id}, format="json")
    assert room.status_code == 201
    assert room.data["department_name"] == department.name


def test_doctor_directory_filters_by_specialty(api, patient, doctor, other_doctor, specialty):
    authenticate(api, patient.user.email)
    response = api.get(f"/api/v1/doctors/?specialty={specialty.id}")
    assert response.status_code == 200
    assert response.data["count"] == 2
    names = {item["display_name"] for item in response.data["results"]}
    assert "Dr Amadou Diallo" in names


def test_admin_can_change_doctor_room(api, admin_user, doctor, department):
    from apps.organization.models import Room

    new_room = Room.objects.create(code="B-777", department=department)
    authenticate(api, admin_user.email)
    response = api.patch(
        f"/api/v1/admin/doctors/{doctor.id}/", {"room": new_room.id}, format="json"
    )
    assert response.status_code == 200
    doctor.refresh_from_db()
    assert doctor.room == new_room
