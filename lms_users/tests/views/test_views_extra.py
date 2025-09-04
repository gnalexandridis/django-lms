from django.test import TestCase, override_settings


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
