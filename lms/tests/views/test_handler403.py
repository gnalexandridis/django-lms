from django.test import TestCase


class Handler403Tests(TestCase):
    def test_handler403_is_callable(self):
        # Importing lms.urls should expose handler403 callable
        from django.test.client import RequestFactory

        from lms import urls as lms_urls

        rf = RequestFactory()
        req = rf.get("/forbidden")
        resp = lms_urls.handler403(req, Exception("boom"))
        self.assertEqual(resp.status_code, 403)
