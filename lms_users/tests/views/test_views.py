# lms_users/tests/test_views_login.py
from django.test import TestCase, override_settings
from django.urls import reverse
from lms_users.models import Roles, User


class LoginRouteTests(TestCase):
    def test_login_url_is_resolvable(self):
        # Θα χρειαστεί να ορίσεις namespace/urls στο lms_users.urls
        url = reverse("lms_users:login")
        self.assertTrue(url.endswith("/login/") or url.endswith("/login"))

    @override_settings(E2E_TEST_LOGIN=False)
    def test_login_redirects_to_oidc_provider_when_test_login_disabled(self):
        r = self.client.get(reverse("lms_users:login"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].endswith("/oidc/authenticate/"))

    @override_settings(E2E_TEST_LOGIN=True)
    def test_test_login_form_is_available_when_flag_enabled(self):
        r = self.client.get(reverse("lms_users:test_login"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Δοκιμαστική Σύνδεση")
        # basic POST creates/logs in a user for dev/e2e
        r2 = self.client.post(
            reverse("lms_users:test_login"),
            {"username": "dev", "password": "pass", "role": "TEACHER"},
        )
        self.assertIn(r2.status_code, (302, 303))

    @override_settings(E2E_TEST_LOGIN=False)
    def test_login_route_redirects_when_test_login_off(self):
        r = self.client.get(reverse("lms_users:login"))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].endswith("/oidc/authenticate/"))

    @override_settings(E2E_TEST_LOGIN=False)
    def test_test_login_forbidden_when_flag_disabled(self):
        r = self.client.get(reverse("lms_users:test_login"))
        self.assertEqual(r.status_code, 403)
        self.assertIn("disabled", r.content.decode().lower())


class TestUserViews(TestCase):
    @override_settings(E2E_TEST_LOGIN=False)
    def test_login_redirects_to_oidc_integration_when_test_login_off(self):
        resp = self.client.get("/users/login/")
        self.assertEqual(resp.status_code, 302)
        # mozilla-django-oidc authenticate init
        self.assertTrue(resp["Location"].endswith("/oidc/authenticate/"))

    @override_settings(E2E_TEST_LOGIN=False)
    def test_test_login_forbidden_when_disabled(self):
        resp = self.client.get("/users/test-login/")
        self.assertEqual(resp.status_code, 403)

    @override_settings(E2E_TEST_LOGIN=True)
    def test_test_login_get_renders_form_and_post_logs_in(self):
        # GET renders the form
        resp = self.client.get("/users/test-login/")
        self.assertEqual(resp.status_code, 200)
        # POST creates user and logs in
        resp2 = self.client.post(
            "/users/test-login/",
            {"username": "coverme", "password": "x", "role": "STUDENT"},
            follow=True,
        )
        self.assertEqual(resp2.status_code, 200)


class TestProviderLogout(TestCase):
    @override_settings(OIDC_OP_LOGOUT_ENDPOINT="https://idp/logout", OIDC_RP_CLIENT_ID="abc")
    def test_provider_logout_builds_url(self):
        User.objects.create_user("u", password="x", role=Roles.STUDENT)
        self.client.login(username="u", password="x")
        from lms_users.views import provider_logout

        resp = provider_logout(self.client.request().wsgi_request)  # type: ignore[arg-type]
        self.assertTrue(isinstance(resp, str))
        self.assertIn("https://idp/logout?", resp)
        self.assertIn("client_id=abc", resp)


class LogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u", password="x", role=Roles.STUDENT)
        self.client.login(username="u", password="x")

    def test_logout_post(self):
        r = self.client.post(reverse("lms_users:logout"))
        self.assertIn(r.status_code, (302, 303))
        # subsequent request should be anonymous
        r2 = self.client.get("/")
        self.assertFalse(r2.wsgi_request.user.is_authenticated)

    def test_logout_get_not_allowed(self):
        r = self.client.get(reverse("lms_users:logout"))
        self.assertEqual(r.status_code, 405)
