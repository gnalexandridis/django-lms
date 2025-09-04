from django.test import TestCase, override_settings


class TestUrlsExtras(TestCase):
    @override_settings(DEBUG=False)
    def test_handler403_function_exists(self):
        # Ensure handler callable returns 403
        from lms.urls import handler403

        resp = handler403(self.client.request().wsgi_request)  # type: ignore[arg-type]
        self.assertEqual(resp.status_code, 403)
