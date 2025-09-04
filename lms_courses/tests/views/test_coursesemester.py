from datetime import date

from django.test import TestCase
from django.urls import reverse

from lms_courses.models import Course, CourseSemester, LabSession
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


class CourseSemesterCreateViewTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="t1", password="x")
        self.teacher.role = "TEACHER"
        self.teacher.save()
        self.course = Course.objects.create(code="CS401", title="Programming I")

    def test_get_shows_form(self):
        self.client.login(username="t1", password="x")
        resp = self.client.get(reverse("lms_courses_teacher:course_semester_teacher_create"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("<form", html)
        self.assertIn('name="course"', html)
        self.assertIn('name="year"', html)

    def test_post_creates_course_semester_and_redirects(self):
        self.client.login(username="t1", password="x")
        resp = self.client.post(
            reverse("lms_courses_teacher:course_semester_teacher_create"),
            data={"course": self.course.pk, "year": 2025, "semester": "WINTER"},
            follow=True,
        )
        self.assertRedirects(resp, reverse("lms_courses_teacher:course_semester_list_teacher"))
        self.assertTrue(
            CourseSemester.objects.filter(
                course=self.course, year=2025, owner=self.teacher
            ).exists()
        )

    def test_prevents_duplicate_for_same_owner_course_semester(self):
        self.client.login(username="t1", password="x")
        CourseSemester.objects.create(
            course=self.course, year=2025, semester="WINTER", owner=self.teacher
        )

        resp = self.client.post(
            reverse("lms_courses_teacher:course_semester_teacher_create"),
            data={"course": self.course.pk, "year": 2025, "semester": "WINTER"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("already exists", resp.content.decode())

    def test_post_invalid_year_shows_error(self):
        self.client.login(username="t1", password="x")
        resp = self.client.post(
            reverse("lms_courses_teacher:course_semester_teacher_create"),
            data={"course": self.course.pk, "year": 1800, "semester": "WINTER"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("year", resp.content.decode())
        self.assertIn("Ensure this value is greater than or equal to 2000", resp.content.decode())

    def test_post_missing_fields_shows_error(self):
        self.client.login(username="t1", password="x")
        resp = self.client.post(
            reverse("lms_courses_teacher:course_semester_teacher_create"),
            data={"course": self.course.pk},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("This field is required", resp.content.decode())

    def test_post_invalid_semester_shows_error(self):
        self.client.login(username="t1", password="x")
        resp = self.client.post(
            reverse("lms_courses_teacher:course_semester_teacher_create"),
            data={"course": self.course.pk, "year": 2025, "semester": "SUMMER"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Select a valid choice", resp.content.decode())


class CourseSemesterDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = User.objects.create_user("t1", password="x")
        cls.t1.role = "TEACHER"
        cls.t1.save()
        cls.t2 = User.objects.create_user("t2", password="x")
        cls.t2.role = "TEACHER"
        cls.t2.save()

        cls.c1 = Course.objects.create(code="CS401", title="Programming I")
        cls.c2 = Course.objects.create(code="CS402", title="Programming II")

        cls.cy1 = CourseSemester.objects.create(
            course=cls.c1, year=2025, semester="WINTER", owner=cls.t1
        )
        cls.cy2 = CourseSemester.objects.create(
            course=cls.c2, year=2025, semester="WINTER", owner=cls.t2
        )

        LabSession.objects.create(
            course_semester=cls.cy1, name="Lab A", week=1, date=date(2025, 1, 7)
        )
        LabSession.objects.create(
            course_semester=cls.cy1, name="Lab A", week=2, date=date(2025, 1, 14)
        )

    def test_requires_login(self):
        url = reverse(
            "lms_courses_teacher:course_semester_teacher_detail", kwargs={"pk": self.cy1.pk}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_owner_sees_own_course_semester_with_labs_sessions(self):
        self.client.login(username="t1", password="x")
        url = reverse(
            "lms_courses_teacher:course_semester_teacher_detail", kwargs={"pk": self.cy1.pk}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("CS401", html)
        self.assertIn("Programming I", html)
        self.assertIn("2025", html)
        self.assertIn('data-testid="add-lab-session"', html)
        self.assertIn("Week 1", html)
        self.assertIn("Week 2", html)
        self.assertIn('data-testid="final-assignment-section"', html)
        self.assertIn('data-testid="create-final-assignment"', html)

    def test_non_owner_gets_404(self):
        self.client.login(username="t1", password="x")
        url = reverse(
            "lms_courses_teacher:course_semester_teacher_detail", kwargs={"pk": self.cy2.pk}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
