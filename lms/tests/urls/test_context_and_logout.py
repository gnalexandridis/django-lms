from django.test import TestCase, override_settings
from django.urls import reverse


class TestContextLoginLink(TestCase):
    @override_settings(E2E_TEST_LOGIN=True)
    def test_login_link_points_to_test_login(self):
        # LOGIN_URL is computed at import-time, so directly hit the login view
        resp = self.client.get(reverse("lms_users:login"))
        # In E2E mode, login view redirects to test-login
        self.assertIn(resp.status_code, (302, 303))
        self.assertIn(reverse("lms_users:test_login"), resp.headers.get("Location", ""))

    @override_settings(E2E_TEST_LOGIN=False)
    def test_login_link_points_to_login(self):
        resp = self.client.get("/")
        # Anonymous users are redirected to the normal login route
        self.assertIn(resp.status_code, (302, 303))
        self.assertIn(reverse("lms_users:login"), resp.headers.get("Location", ""))


class TestLogoutRoute(TestCase):
    @override_settings(E2E_TEST_LOGIN=True)
    def test_logout_post_redirects_home(self):
        # POST without login simply redirects; route exists
        resp = self.client.post(reverse("lms_users:logout"))
        self.assertIn(resp.status_code, (302, 303))
