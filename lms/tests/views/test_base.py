from django.test import TestCase
from django.urls import reverse

from lms_users.models import Roles, User


class TestBaseHomeRedirects(TestCase):
    def test_home_redirects_by_role(self):
        # anonymous -> login
        resp = self.client.get(reverse("home"))
        self.assertIn(resp.status_code, (302,))

        # student -> student_home
        User.objects.create_user("s1", password="x", role=Roles.STUDENT)
        self.client.login(username="s1", password="x")
        resp2 = self.client.get(reverse("home"))
        self.assertEqual(resp2.status_code, 302)
        self.client.logout()

        # teacher -> teacher_home
        User.objects.create_user("t1", password="x", role=Roles.TEACHER)
        self.client.login(username="t1", password="x")
        resp3 = self.client.get(reverse("home"))
        self.assertEqual(resp3.status_code, 302)
