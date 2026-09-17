"""Utilitaires partagés par les tests (mot de passe et authentification API)."""

PASSWORD = "TestPassw0rd!2026"


def authenticate(api, email, password=PASSWORD):
    """Authentifie le client de test et pose l'en-tête Bearer."""
    response = api.post(
        "/api/v1/auth/login/", {"email": email, "password": password}, format="json"
    )
    assert response.status_code == 200, response.data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return response.data
