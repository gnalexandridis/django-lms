from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Roles
from .permissions import has_role


def role_required(*allowed_roles: str | Roles):
    """
    Usage:
    @role_required("TEACHER", "STUDENT")
    or
    @role_required(Roles.TEACHER, Roles.STUDENT)
    def my_view(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if has_role(user, allowed_roles):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("Insufficient role")

        return _wrapped

    return decorator
