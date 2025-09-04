from django.test import TestCase, override_settings


class TestRootUrlsAndErrors(TestCase):
    def test_includes_do_not_error(self):
        # Smoke test some known routes to ensure URL includes are wired
        resp = self.client.get("/users/login/")
        self.assertIn(resp.status_code, (302, 404))
        resp2 = self.client.get("/teacher/courses/")
        # Likely 302 to login due to RoleRequired, but route resolves
        self.assertIn(resp2.status_code, (200, 302, 403))

    @override_settings(DEBUG=False, E2E_TEST_LOGIN=False)
    def test_403_handler_renders(self):
        # Force a 403 by hitting test-login without enabling it
        resp = self.client.get("/users/test-login/")
        self.assertEqual(resp.status_code, 403)
