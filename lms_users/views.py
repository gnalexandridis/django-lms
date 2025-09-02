from django.conf import settings
from django.contrib.auth import login, logout
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods

from lms_users.typing_utils import UserModel as U


def login_view(request):
    # Only consult E2E_TEST_LOGIN now; no OIDC_ENABLED flag.
    if getattr(settings, "E2E_TEST_LOGIN", False):
        # During tests/dev, use the in-app test login form
        return redirect(reverse("lms_users:test_login"))
    # Otherwise, bounce to the OIDC initiation route (configured via mozilla-django-oidc)
    return redirect(reverse("oidc_authentication_init"))


@require_http_methods(["GET", "POST"])
def test_login_view(request):
    if not getattr(settings, "E2E_TEST_LOGIN", False):
        return HttpResponseForbidden("Test login disabled")

    if request.method == "POST":
        username = request.POST.get("username") or "dev"
        password = request.POST.get("password") or "x"
        role = request.POST.get("role") or "STUDENT"
        user, created = U.objects.get_or_create(username=username, defaults={"role": role})
        if not created and hasattr(user, "role"):
            user.role = role
        user.set_password(password)
        user.save()
        # When multiple auth backends are configured, pass a concrete backend
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("/")  # any page; E2E just waits for load

    # GET: render simple form
    return render(request, "lms_users/test_login.html")


@require_http_methods(["POST"])  # keep simple; safety against CSRF is enabled by default
def logout_view(request):
    logout(request)
    return redirect("/")


def provider_logout(request):
    logout_ep = getattr(settings, "OIDC_OP_LOGOUT_ENDPOINT", "")
    return_to = request.build_absolute_uri(reverse("home"))
    params = {"post_logout_redirect_uri": return_to}
    params["client_id"] = getattr(settings, "OIDC_RP_CLIENT_ID", "")
    return f"{logout_ep}?{urlencode(params)}"
