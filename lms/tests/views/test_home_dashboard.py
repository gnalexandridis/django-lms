from django.test import TestCase

from lms_users.models import Roles, User


class TestHomeDashboard(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teach", password="x", role=Roles.TEACHER)
        self.client.login(username="teach", password="x")

    def test_home_for_student_simple(self):
        self.client.logout()
        User.objects.create_user(username="stud", password="x", role=Roles.STUDENT)
        self.client.login(username="stud", password="x")
        resp = self.client.get("/", follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-testid="student-total-courses"')
