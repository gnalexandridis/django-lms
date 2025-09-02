from django.conf import settings
from django.urls import reverse

from .models import Roles


def roles(request):
    """Expose Roles enum to templates and convenience flags for current user."""
    user = getattr(request, "user", None)
    role = getattr(user, "role", None) if user and user.is_authenticated else None
    # Dynamic login entry point: use test-login in E2E mode, otherwise normal login
    login_link = (
        reverse("lms_users:test_login")
        if getattr(settings, "E2E_TEST_LOGIN", False)
        else reverse("lms_users:login")
    )
    return {
        "ROLES": Roles,
        "USER_ROLE": role,
        "IS_TEACHER": role == Roles.TEACHER,
        "IS_STUDENT": role == Roles.STUDENT,
        "LOGIN_LINK": login_link,
    }
