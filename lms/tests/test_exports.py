from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from lms_courses.models import Course, CourseSemester, LabSession
from lms_users.models import Roles, User


class TestDashboardExports(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("teach", password="x", role=Roles.TEACHER)
        self.client.login(username="teach", password="x")

        c = Course.objects.create(code="CSX", title="XLSX Course")
        self.cs1 = CourseSemester.objects.create(
            course=c,
            year=2025,
            semester="WINTER",
            owner=self.teacher,
        )
        # session within 7 days window
        LabSession.objects.create(
            name="Lab1",
            week=1,
            date=date.today() + timedelta(days=2),
            course_semester=self.cs1,
        )

    def test_export_dashboard_csv(self):
        url = reverse("teacher_export_dashboard") + f"?days=7&course={self.cs1.pk}&format=csv"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])  # type: ignore[index]
        body = resp.content.decode("utf-8-sig")
        # Headers and some keys
        self.assertIn("key,value", body)
        self.assertIn("active_courses", body)
        self.assertIn("course_code,course_title,year,students", body)
        self.assertIn("CSX", body)

    def test_export_dashboard_xlsx(self):
        url = reverse("teacher_export_dashboard") + f"?days=7&course={self.cs1.pk}&format=xlsx"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            resp["Content-Type"],
        )  # type: ignore[index]
        # Basic sanity: non-empty binary and filename disposition
        self.assertGreater(len(resp.content), 100)  # binary workbook should be >100 bytes
        self.assertIn(
            "attachment; filename=dashboard_stats_",
            resp["Content-Disposition"],
        )  # type: ignore[index]

    def test_export_dashboard_forbidden_for_student(self):
        self.client.logout()
        User.objects.create_user("stud", password="x", role=Roles.STUDENT)
        self.client.login(username="stud", password="x")
        url = reverse("teacher_export_dashboard")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)
