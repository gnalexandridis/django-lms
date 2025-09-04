from django.test import TestCase, override_settings
from django.urls import reverse


class TestUrlsExtras(TestCase):
    def test_export_url_exists(self):
        resp = self.client.get(reverse("teacher_export_dashboard"))
        # Not authenticated -> should redirect to login
        self.assertIn(resp.status_code, (302, 403))

    @override_settings(DEBUG=False)
    def test_handler403_function_exists(self):
        # Ensure handler callable returns 403
        from lms.urls import handler403

        resp = handler403(self.client.request().wsgi_request)  # type: ignore[arg-type]
        self.assertEqual(resp.status_code, 403)
