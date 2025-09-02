from __future__ import annotations

from typing import Any

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .models import Roles
from .typing_utils import UserModel as UserT


class KeycloakOIDCBackend(OIDCAuthenticationBackend):
    """
    OIDC authentication backend integrating with Keycloak.

    - Uses preferred_username/email/sub as the username
    - Maps realm roles to our internal Roles enum
    - Creates/updates our custom User model
    """

    def filter_users_by_claims(self, claims: dict[str, Any]):  # type: ignore[override]
        User = UserT
        username = claims.get("preferred_username") or claims.get("email") or claims.get("sub")
        if not username:
            return User.objects.none()
        return User.objects.filter(username=str(username))

    def create_user(self, claims: dict[str, Any]):  # type: ignore[override]
        User = UserT
        username = claims.get("preferred_username") or claims.get("email") or claims.get("sub")
        email = claims.get("email")
        if not username:
            # Fallback to sub if everything else fails
            username = claims.get("sub")
        user = User.objects.create_user(username=str(username), email=email)
        # Apply role mapping
        user.role = self._role_from_claims(claims)
        user.save()
        return user

    def update_user(self, user: UserT, claims: dict[str, Any]):  # type: ignore[override]
        email = claims.get("email")
        if email and getattr(user, "email", None) != email:
            user.email = email
        new_role = self._role_from_claims(claims)
        if new_role and getattr(user, "role", None) != new_role:
            user.role = new_role
        user.save()
        return user

    def _role_from_claims(self, claims: dict[str, Any]) -> str:
        """Map Keycloak realm roles to our internal Roles enum."""
        groups = claims.get("groups") or {}
        lower = {r.lower() for r in groups}
        if "teacher" in lower:
            return Roles.TEACHER
        if "student" in lower:
            return Roles.STUDENT
        # Default to student if nothing explicit is present
        return Roles.STUDENT
