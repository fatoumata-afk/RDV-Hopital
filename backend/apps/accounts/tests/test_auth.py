import pytest

from apps.accounts.models import User, UserRole
from apps.common.test_utils import PASSWORD, authenticate

pytestmark = pytest.mark.django_db


def test_patient_registration_creates_profile_and_tokens(api):
    response = api.post(
        "/api/v1/auth/register/",
        {
            "email": "nouvelle@test.local",
            "password": PASSWORD,
            "first_name": "Nouvelle",
            "last_name": "Patiente",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["user"]["role"] == UserRole.PATIENT
    assert response.data["user"]["profile"]["medical_record_number"]
    assert "access" in response.data and "refresh" in response.data


def test_registration_rejects_duplicate_email(api, patient):
    response = api.post(
        "/api/v1/auth/register/",
        {
            "email": patient.user.email,
            "password": PASSWORD,
            "first_name": "Double",
            "last_name": "Compte",
        },
        format="json",
    )
    assert response.status_code == 400


def test_registration_rejects_weak_password(api):
    response = api.post(
        "/api/v1/auth/register/",
        {
            "email": "faible@test.local",
            "password": "1234",
            "first_name": "Mot",
            "last_name": "Faible",
        },
        format="json",
    )
    assert response.status_code == 400


def test_login_returns_role_and_profile(api, doctor):
    data = authenticate(api, doctor.user.email)
    assert data["user"]["role"] == UserRole.DOCTOR
    assert data["user"]["profile"]["specialty_name"] == "Cardiologie"


def test_login_with_wrong_password_fails(api, patient):
    response = api.post(
        "/api/v1/auth/login/",
        {"email": patient.user.email, "password": "mauvais-mot-de-passe"},
        format="json",
    )
    assert response.status_code == 401


def test_me_requires_authentication(api):
    assert api.get("/api/v1/auth/me/").status_code == 401


def test_patient_cannot_escalate_role_via_me(api, patient):
    authenticate(api, patient.user.email)
    response = api.patch("/api/v1/auth/me/", {"role": UserRole.ADMIN}, format="json")
    assert response.status_code == 200
    patient.user.refresh_from_db()
    assert patient.user.role == UserRole.PATIENT


def test_patient_can_update_own_profile(api, patient):
    authenticate(api, patient.user.email)
    response = api.patch(
        "/api/v1/auth/me/",
        {"phone": "+224 620 00 00 00", "profile": {"address": "Conakry"}},
        format="json",
    )
    assert response.status_code == 200
    patient.refresh_from_db()
    assert patient.address == "Conakry"
    assert patient.user.phone == "+224 620 00 00 00"


def test_change_password(api, patient):
    authenticate(api, patient.user.email)
    response = api.post(
        "/api/v1/auth/change-password/",
        {"current_password": PASSWORD, "new_password": "AutreMotDePasse!99"},
        format="json",
    )
    assert response.status_code == 204
    patient.user.refresh_from_db()
    assert patient.user.check_password("AutreMotDePasse!99")


def test_only_admin_can_create_staff_accounts(api, patient, admin_user, specialty, department):
    payload = {
        "role": UserRole.DOCTOR,
        "email": "dr.nouveau@test.local",
        "password": PASSWORD,
        "first_name": "Nouveau",
        "last_name": "Medecin",
        "license_number": "ORD-99",
        "specialty": specialty.id,
        "department": department.id,
    }
    authenticate(api, patient.user.email)
    assert api.post("/api/v1/admin/users/", payload, format="json").status_code == 403

    authenticate(api, admin_user.email)
    response = api.post("/api/v1/admin/users/", payload, format="json")
    assert response.status_code == 201
    created = User.objects.get(email="dr.nouveau@test.local")
    assert created.role == UserRole.DOCTOR
    assert created.must_change_password is True
