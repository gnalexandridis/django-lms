from datetime import date

from django.test import TestCase
from django.urls import reverse

from lms_courses.models import Course, CourseSemester, LabSession
from lms_users.typing_utils import User


class LabSessionCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = User.objects.create_user("t1", password="x")
        cls.t1.role = "TEACHER"
        cls.t1.save()
        cls.t2 = User.objects.create_user("t2", password="x")
        cls.t2.role = "TEACHER"
        cls.t2.save()

        cls.c1 = Course.objects.create(code="CS401", title="Programming I")
        cls.cy1 = CourseSemester.objects.create(course=cls.c1, year=2025, owner=cls.t1)

    def test_get_shows_form(self):
        self.client.login(username="t1", password="x")
        url = reverse("lms_courses_teacher:lab_session_create", kwargs={"pk": self.cy1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('data-testid="labsession-form"', html)
        self.assertIn('name="week"', html)
        self.assertIn('name="date"', html)

    def test_post_creates_session_and_redirects(self):
        self.client.login(username="t1", password="x")
        url = reverse("lms_courses_teacher:lab_session_create", kwargs={"pk": self.cy1.pk})
        resp = self.client.post(
            url,
            data={"name": "Lab A", "week": 1, "date": "2025-01-07"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            LabSession.objects.filter(
                course_semester=self.cy1, week=1, date=date(2025, 1, 7)
            ).exists()
        )

    def test_duplicate_week_and_name_stays_on_form_with_error(self):
        self.client.login(username="t1", password="x")
        LabSession.objects.create(
            course_semester=self.cy1,
            name="Lab A",
            week=1,
            date=date(2025, 1, 7),
        )
        url = reverse("lms_courses_teacher:lab_session_create", kwargs={"pk": self.cy1.pk})
        resp = self.client.post(url, data={"name": "Lab A", "week": 1, "date": "2025-01-14"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("already", resp.content.decode().lower())

    def test_post_missing_date_shows_error(self):
        self.client.login(username="t1", password="x")
        url = reverse("lms_courses_teacher:lab_session_create", kwargs={"pk": self.cy1.pk})
        resp = self.client.post(url, data={"name": "Lab A", "week": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("This field is required", resp.content.decode())

    def test_sessions_ordered_by_week(self):
        self.client.login(username="t1", password="x")
        LabSession.objects.create(
            course_semester=self.cy1,
            name="Lab A",
            week=2,
            date=date(2025, 1, 14),
        )
        LabSession.objects.create(
            course_semester=self.cy1,
            name="Lab A",
            week=1,
            date=date(2025, 1, 7),
        )
        sessions = LabSession.objects.filter(course_semester=self.cy1).order_by("week")
        weeks = [s.week for s in sessions]
        self.assertEqual(weeks, [1, 2])

    def test_unauthenticated_user_redirected(self):
        url = reverse("lms_courses_teacher:lab_session_create", kwargs={"pk": self.cy1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
