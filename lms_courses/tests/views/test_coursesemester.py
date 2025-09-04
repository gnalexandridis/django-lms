from django.test import TestCase
from django.urls import reverse

from lms_courses.models import Course, CourseSemester
from lms_users.typing_utils import User


class CourseSemesterListViewTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="t1", password="x")
        self.teacher.role = "TEACHER"
        self.teacher.save()

        self.other = User.objects.create_user(username="t2", password="x")
        self.other.role = "TEACHER"
        self.other.save()

        self.course = Course.objects.create(code="CS401", title="Programming I")
        self.course2 = Course.objects.create(code="CS402", title="Programming II")

        CourseSemester.objects.create(
            course=self.course, year=2025, semester="WINTER", owner=self.teacher
        )
        CourseSemester.objects.create(
            course=self.course2, year=2025, semester="WINTER", owner=self.other
        )

    def test_requires_login(self):
        resp = self.client.get(reverse("lms_courses_teacher:course_semester_list_teacher"))
        self.assertEqual(resp.status_code, 302)

    def test_lists_only_my_course_semesters_and_shows_create_button(self):
        self.client.login(username="t1", password="x")
        resp = self.client.get(reverse("lms_courses_teacher:course_semester_list_teacher"))
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn("Programming I", content)
        self.assertNotIn("Programming II", content)
        self.assertIn('data-testid="create-course-semester"', content)
