from django.test import TestCase
from django.urls import reverse

from lms_courses.models import Course, CourseSemester, LabSession
from lms_users.models import Roles, User


class TestLabSessionManageView(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="t1", password="x", role=Roles.TEACHER)
        self.client.login(username="t1", password="x")
        self.course = Course.objects.create(code="CS401", title="Programming I")
        self.cs = CourseSemester.objects.create(
            course=self.course, year=2025, semester="WINTER", owner=self.teacher
        )
        self.session = LabSession.objects.create(
            name="Lab A", week=1, date="2025-01-07", course_semester=self.cs
        )

    def test_get_manage_page(self):
        url = reverse("lms_courses_teacher:lab_session_manage", args=[self.cs.pk, self.session.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Διαχείριση Συνεδρίας")