from django.test import TestCase
from django.urls import reverse

from lms_users.models import Roles, User


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
