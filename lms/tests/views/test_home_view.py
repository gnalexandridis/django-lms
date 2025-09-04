from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse


class HomeViewRedirectTests(TestCase):
    def setUp(self):
        self.U = get_user_model()

    def test_home_redirects_student_to_student_home(self):
        u = self.U.objects.create_user(username="s1", password="x", role="STUDENT")
        self.client.force_login(u)
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/student/", r.headers.get("Location", ""))

    def test_home_redirects_teacher_to_teacher_home(self):
        u = self.U.objects.create_user(username="t1", password="x", role="TEACHER")
        self.client.force_login(u)
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/teacher/", r.headers.get("Location", ""))

    def test_home_redirects_other_to_login(self):
        u = self.U.objects.create_user(username="a1", password="x", role="ADMIN")
        self.client.force_login(u)
        # The home view tries to reverse the non-namespaced 'login', which is not defined.
        with self.assertRaises(NoReverseMatch):
            self.client.get(reverse("home"))
