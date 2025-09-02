from __future__ import annotations

from typing import Iterable, Sequence

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Roles


def normalize_roles(roles: Iterable[str | Roles] | None) -> tuple[str, ...]:
    if not roles:
        return tuple()
    norm: list[str] = []
    for r in roles:
        if isinstance(r, Roles):
            norm.append(r.value)
        else:
            norm.append(str(r))
    return tuple(norm)


def has_role(user, roles: Iterable[str | Roles] | None) -> bool:
    """Return True if user has any of the given roles.

    - Superusers and staff are always allowed.
    - If roles is empty/None, allow (no restriction).
    """
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    allowed = normalize_roles(roles)
    if not allowed:
        return True
    return getattr(user, "role", None) in allowed


def is_student(user) -> bool:
    return has_role(user, (Roles.STUDENT,))


def is_teacher(user) -> bool:
    return has_role(user, (Roles.TEACHER,))


class RoleRequiredMixin(LoginRequiredMixin):
    """CBV mixin enforcing that the authenticated user has one of allowed roles.

    Usage:
        class MyView(RoleRequiredMixin, View):
            allowed_roles = (Roles.TEACHER, Roles.STUDENT)
    """

    allowed_roles: Sequence[str | Roles] | None = None

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        # LoginRequiredMixin handles anonymous users
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not has_role(request.user, self.allowed_roles):
            raise PermissionDenied("Insufficient role")
        return super().dispatch(request, *args, **kwargs)


class OwnerRequiredMixin(RoleRequiredMixin):
    """CBV mixin to load an object owned by the current user or return 404.

    Configure:
      - model: The model class to load (or override get_owned_queryset).
      - owner_field: Field name of the owner relation (default: "owner").
      - lookup_url_kwarg: URL kwarg containing the pk (default: "pk").
      - context_object_name: Attribute name to expose on self (default: "object").

    This runs after role checks and before delegating to the base dispatch.
    """

    model = None
    owner_field = "owner"
    lookup_url_kwarg = "pk"
    context_object_name = "object"

    def get_owned_queryset(self):
        if self.model is None:  # pragma: no cover - guarded by usage
            raise ImproperlyConfigured(
                "OwnerRequiredMixin requires 'model' or 'get_owned_queryset'."
            )
        return self.model._default_manager.all()

    def get_owned_object(self):
        pk = self.kwargs.get(self.lookup_url_kwarg)  # type: ignore[attr-defined]
        qs = self.get_owned_queryset()
        filters = {"pk": pk, self.owner_field: self.request.user}
        obj = get_object_or_404(qs, **filters)
        self.object = obj  # type: ignore[assignment]
        setattr(self, self.context_object_name, obj)
        return obj

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        # role check first
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not has_role(request.user, self.allowed_roles):
            raise PermissionDenied("Insufficient role")
        # then ownership
        self.get_owned_object()
        return super(RoleRequiredMixin, self).dispatch(request, *args, **kwargs)
