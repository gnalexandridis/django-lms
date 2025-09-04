from datetime import date, timedelta

from django.core.cache import cache
from django.test import TestCase

from lms_courses.models import Course, CourseSemester, LabSession
from lms_users.models import Roles, User


class TestHomeDashboard(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teach", password="x", role=Roles.TEACHER)
        self.client.login(username="teach", password="x")

    def test_dashboard_renders_for_teacher(self):
        # No data, but the stat cards should render
        # Teacher visiting '/' will be redirected to teacher_home
        resp = self.client.get("/", follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-testid="stat-active-courses"')
        self.assertContains(resp, 'data-testid="stat-unique-students"')
        self.assertContains(resp, 'data-testid="stat-upcoming-labs"')

    def test_course_rows_present(self):
        c = Course.objects.create(code="CS100", title="Intro")
        CourseSemester.objects.create(course=c, year=2025, semester="WINTER", owner=self.teacher)
        resp = self.client.get("/", follow=True)
        self.assertContains(resp, "CS100")
        self.assertContains(resp, "Intro")

    def test_filters_and_caching(self):
        cache.clear()
        # Two courses, only one has a lab in the next 3 days
        c1 = Course.objects.create(code="CS101", title="Algo")
        c2 = Course.objects.create(code="CS102", title="DB")
        cs1 = CourseSemester.objects.create(
            course=c1, year=2025, semester="WINTER", owner=self.teacher
        )
        cs2 = CourseSemester.objects.create(
            course=c2, year=2025, semester="WINTER", owner=self.teacher
        )

        # Lab for cs1 tomorrow (within 3 days)
        LabSession.objects.create(
            name="L1",
            week=1,
            date=date.today() + timedelta(days=1),
            course_semester=cs1,
        )
        # Lab for cs2 in 20 days (outside 3 days)
        LabSession.objects.create(
            name="L2",
            week=1,
            date=date.today() + timedelta(days=20),
            course_semester=cs2,
        )

        # First request computes and caches
        resp1 = self.client.get(f"/teacher/?days=3&course={cs1.pk}", follow=True)
        self.assertEqual(resp1.status_code, 200)
        # Upcoming labs should count only cs1 within 3 days
        self.assertIn("upcoming_labs", resp1.context)
        self.assertEqual(resp1.context["upcoming_labs"], 1)
        # Only one course row due to filter
        content1 = resp1.content.decode("utf-8")
        self.assertIn("CS101", content1)
        # Ensure CS102 is not present as a table cell (it will still appear in the filter dropdown)
        self.assertNotIn('<td class="px-4 py-2">CS102</td>', content1)

        # Second request hits cache branch
        resp2 = self.client.get(f"/teacher/?days=3&course={cs1.pk}", follow=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.context["upcoming_labs"], 1)

        # Invalid days falls back to 7
        resp3 = self.client.get("/teacher/?days=abc", follow=True)
        self.assertEqual(resp3.status_code, 200)
        self.assertIn("filter_days", resp3.context)
        self.assertEqual(resp3.context["filter_days"], 7)

    def test_home_for_student_simple(self):
        self.client.logout()
        User.objects.create_user(username="stud", password="x", role=Roles.STUDENT)
        self.client.login(username="stud", password="x")
        resp = self.client.get("/", follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-testid="student-total-courses"')

    def test_invalid_course_filter_ignored(self):
        cache.clear()
        c1 = Course.objects.create(code="CS201", title="Math")
        c2 = Course.objects.create(code="CS202", title="Physics")
        CourseSemester.objects.create(course=c1, year=2025, semester="WINTER", owner=self.teacher)
        CourseSemester.objects.create(course=c2, year=2025, semester="WINTER", owner=self.teacher)
        resp = self.client.get("/?course=999999&days=7", follow=True)
        content = resp.content.decode("utf-8")
        self.assertIn("CS201", content)
        self.assertIn("CS202", content)
