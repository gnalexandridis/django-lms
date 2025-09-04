# lms_users/tests/test_views_login.py
from django.test import TestCase, override_settings
from django.urls import reverse


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
