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

    def test_post_attendance_and_grade(self):
        s1 = User.objects.create_user(username="s1", password="x", role=Roles.STUDENT)
        self.cs.students.add(s1)
        url = reverse("lms_courses_teacher:lab_session_manage", args=[self.cs.pk, self.session.pk])
        data = {
            f"present_{s1.id}": "on",
            f"grade_{s1.id}": "8",
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        # counters via properties
        self.session.refresh_from_db()
        self.assertEqual(self.session.present_count, 1)
        self.assertEqual(self.session.graded_count, 1)

        # Now GET again and ensure form is prefilled
        resp2 = self.client.get(url)
        self.assertEqual(resp2.status_code, 200)
        # Checkbox for presence should be checked
        self.assertContains(resp2, f'name="present_{s1.id}"')
        self.assertContains(resp2, f'name="present_{s1.id}" checked')
        # Grade field should have value=8
        self.assertContains(resp2, f'name="grade_{s1.id}"')
        self.assertContains(resp2, f'name="grade_{s1.id}" value="8"')
