from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from django.conf import settings


class KeycloakClient:
    def __init__(self) -> None:
        self.base_url: str = settings.KEYCLOAK_BASE_URL.rstrip("/")
        self.realm: str = settings.KEYCLOAK_REALM
        # Prefer dedicated admin client if provided; fall back to RP client
        self.client_id: str = getattr(settings, "KEYCLOAK_ADMIN_CLIENT_ID", None) or getattr(
            settings, "OIDC_RP_CLIENT_ID", ""
        )
        self.client_secret: str = getattr(
            settings, "KEYCLOAK_ADMIN_CLIENT_SECRET", None
        ) or getattr(settings, "OIDC_RP_CLIENT_SECRET", "")
        self.verify_ssl: bool = getattr(settings, "OIDC_VERIFY_SSL", True)
        self.timeout: int = getattr(settings, "KEYCLOAK_TIMEOUT", 5)

    def _token_url(self) -> str:
        return f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"

    def _admin_url(self, path: str) -> str:
        return f"{self.base_url}/admin/realms/{self.realm}{path}"

    def get_admin_token(self) -> Optional[str]:
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            r = requests.post(
                self._token_url(), data=data, verify=self.verify_ssl, timeout=self.timeout
            )
            if r.status_code != 200:
                return None
            return r.json().get("access_token")
        except Exception:
            return None

    # ---- Group helpers ----
    def get_group_id_by_name(self, name: str) -> Optional[str]:
        token = self.get_admin_token()
        if not token:
            return None
        try:
            r = requests.get(
                self._admin_url("/groups"),
                params={"search": name},
                headers={"Authorization": f"Bearer {token}"},
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return None
            groups = r.json() or []
            # Prefer exact (case-insensitive) name match
            for g in groups:
                if str(g.get("name", "")).lower() == name.lower():
                    return g.get("id")
            # Fallback to first
            return groups[0].get("id") if groups else None
        except Exception:
            return None

    def get_group_members(
        self, group_id: str, *, search: Optional[str] = None, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        token = self.get_admin_token()
        if not token:
            return []
        params: Dict[str, Any] = {"first": 0, "max": max_results}
        # Modern Keycloak supports `search` to filter group members
        if search:
            params["search"] = search
        try:
            r = requests.get(
                self._admin_url(f"/groups/{group_id}/members"),
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return []
            users = r.json() or []
            # If server ignored `search`, fallback client-side filter
            if search:
                q = search.lower()
                users = [
                    u
                    for u in users
                    if (
                        q in str(u.get("username", "")).lower()
                        or q in str(u.get("email", "")).lower()
                        or q in str(u.get("firstName", "")).lower()
                        or q in str(u.get("lastName", "")).lower()
                    )
                ]
            return users[:max_results]
        except Exception:
            return []

    def search_users(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        token = self.get_admin_token()
        if not token:
            return []
        try:
            r = requests.get(
                self._admin_url("/users"),
                params={"search": query, "max": max_results},
                headers={"Authorization": f"Bearer {token}"},
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            if r.status_code != 200:
                return []
            return r.json()
        except Exception:
            return []

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        matches = self.search_users(username, max_results=5)
        # Try to find exact username match first
        for u in matches:
            if str(u.get("username", "")).lower() == username.lower():
                return u
        # Fallback to first result
        return matches[0] if matches else None

    def search_users_in_group(
        self, query: str, group_name: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        group_id = self.get_group_id_by_name(group_name)
        if not group_id:
            return []
        return self.get_group_members(group_id, search=query, max_results=max_results)


def search_students(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search for students across local DB and Keycloak (if enabled).

    Returns a list of dicts: {username, full_name, email, source}
    """
    from django.contrib.auth import get_user_model
    from django.db.models import Q

    from lms_users.models import Roles

    results: List[Dict[str, Any]] = []
    User = get_user_model()
    # Local first
    local_q = Q(role=Roles.STUDENT) & (
        Q(username__icontains=query)
        | Q(email__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
    )
    for u in User.objects.filter(local_q).order_by("username")[: max_results // 2]:
        full = f"{getattr(u, 'first_name', '')} {getattr(u, 'last_name', '')}".strip()
        results.append(
            {
                "username": u.username,
                "full_name": full,
                "email": getattr(u, "email", None),
                "source": "local",
            }
        )

    # Keycloak (if OIDC is on)
    if not getattr(settings, "E2E_TEST_LOGIN", False):
        kc = KeycloakClient()
        try:
            group_name = getattr(settings, "KEYCLOAK_STUDENTS_GROUP", "students")
            kc_users = kc.search_users_in_group(query, group_name, max_results=max_results)
        except Exception:
            kc_users = []
        for u in kc_users:
            username = u.get("username")
            if not username:
                continue
            full = f"{u.get('firstName', '')} {u.get('lastName', '')}".strip()
            results.append(
                {
                    "username": username,
                    "full_name": full,
                    "email": u.get("email"),
                    "source": "keycloak",
                }
            )

    # De-duplicate by username preserving order (local wins)
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for r in results:
        if r["username"] in seen:
            continue
        seen.add(r["username"])
        deduped.append(r)
    return deduped[:max_results]


def provision_local_student_from_kc(username: str):
    """Find a Keycloak user and create a local student if not existing.

    Returns the Django user or None if not found / failure.
    """
    from django.contrib.auth import get_user_model

    from lms_users.models import Roles

    User = get_user_model()
    # If already exists locally, return it
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        pass

    client = KeycloakClient()
    kc_user = client.get_user_by_username(username)
    if not kc_user:
        return None

    email = kc_user.get("email")
    first = kc_user.get("firstName")
    last = kc_user.get("lastName")
    user = User.objects.create_user(username=username, email=email)
    # Optional: store names if your model has them (AbstractUser does)
    try:
        if first:
            user.first_name = first
        if last:
            user.last_name = last
    except Exception:
        pass
    # Default role to STUDENT
    try:
        user.role = Roles.STUDENT  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        user.set_unusable_password()
    except Exception:
        pass
    user.save()
    return user
