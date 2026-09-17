"""Permissions de rôle. La véritable isolation des données passe aussi par
le filtrage des querysets dans chaque vue."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import UserRole


class _RolePermission(BasePermission):
    role: str = ""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == self.role)


class IsPatient(_RolePermission):
    role = UserRole.PATIENT


class IsDoctor(_RolePermission):
    role = UserRole.DOCTOR


class IsAgent(_RolePermission):
    role = UserRole.AGENT


class IsAdmin(_RolePermission):
    role = UserRole.ADMIN


class IsAgentOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role in {UserRole.AGENT, UserRole.ADMIN}
        )


class IsAdminOrReadOnly(BasePermission):
    """Lecture pour tout utilisateur authentifié, écriture réservée à l'admin."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role == UserRole.ADMIN
