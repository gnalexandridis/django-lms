from datetime import date

from django.test import TestCase
from django.urls import reverse

from lms_courses.models import Course, CourseSemester, FinalAssignment
from lms_users.typing_utils import User


class FinalAssignmentViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = User.objects.create_user("t1", password="x")
        cls.t1.role = "TEACHER"
        cls.t1.save()
        cls.c1 = Course.objects.create(code="CS401", title="Programming I")
        cls.cy1 = CourseSemester.objects.create(course=cls.c1, year=2025, owner=cls.t1)

    def test_create_get_shows_form(self):
        self.client.login(username="t1", password="x")
        url = reverse("lms_courses_teacher:final_assignment_create", kwargs={"pk": self.cy1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn('data-testid="finalassignment-form"', html)
        self.assertIn('name="title"', html)
        self.assertIn('name="max_grade"', html)
        self.assertIn('name="due_date"', html)

    def test_create_post_creates_and_redirects(self):
        self.client.login(username="t1", password="x")
        url = reverse("lms_courses_teacher:final_assignment_create", kwargs={"pk": self.cy1.pk})
        resp = self.client.post(
            url,
            data={"title": "Final Assignment", "max_grade": 100, "due_date": "2025-02-20"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            FinalAssignment.objects.filter(
                course_semester=self.cy1, title="Final Assignment"
            ).exists()
        )

    def test_detail_hides_create_when_exists_and_shows_edit(self):
        self.client.login(username="t1", password="x")
        FinalAssignment.objects.create(
            course_semester=self.cy1, title="FA", max_grade=100, due_date=date(2025, 2, 20)
        )
        url = reverse(
            "lms_courses_teacher:course_semester_teacher_detail", kwargs={"pk": self.cy1.pk}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("FA", html)
        self.assertIn('data-testid="final-assignment-section"', html)
        self.assertIn('data-testid="edit-final-assignment"', html)
        self.assertNotIn('data-testid="create-final-assignment"', html)

    def test_create_redirects_to_edit_when_exists(self):
        self.client.login(username="t1", password="x")
        FinalAssignment.objects.create(
            course_semester=self.cy1, title="FA", max_grade=100, due_date=date(2025, 2, 20)
        )
        url = reverse("lms_courses_teacher:final_assignment_create", kwargs={"pk": self.cy1.pk})
        resp = self.client.get(url, follow=True)
        self.assertRedirects(
            resp,
            reverse("lms_courses_teacher:final_assignment_edit", kwargs={"pk": self.cy1.pk}),
            fetch_redirect_response=False,
        )

    def test_edit_post_updates_successfully(self):
        self.client.login(username="t1", password="x")
        fa = FinalAssignment.objects.create(
            course_semester=self.cy1, title="FA", max_grade=100, due_date=date(2025, 2, 20)
        )
        url = reverse("lms_courses_teacher:final_assignment_edit", kwargs={"pk": self.cy1.pk})
        resp = self.client.post(
            url,
            data={"title": "FA v2", "max_grade": 90, "due_date": "2025-03-01"},
        )
        self.assertEqual(resp.status_code, 302)
        fa.refresh_from_db()
        self.assertEqual(fa.title, "FA v2")
        self.assertEqual(fa.max_grade, 90)

    def test_edit_invalid_date_stays_on_form(self):
        self.client.login(username="t1", password="x")
        FinalAssignment.objects.create(
            course_semester=self.cy1, title="FA", max_grade=100, due_date=date(2025, 2, 20)
        )
        url = reverse("lms_courses_teacher:final_assignment_edit", kwargs={"pk": self.cy1.pk})
        resp = self.client.post(
            url,
            data={"title": "FA", "max_grade": 100, "due_date": "not-a-date"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("due_date", resp.content.decode())

    def test_non_owner_cannot_create_or_edit(self):
        t2 = User.objects.create_user("t2", password="x")
        t2.role = "TEACHER"
        t2.save()
        self.client.login(username="t2", password="x")
        resp_create = self.client.get(
            reverse("lms_courses_teacher:final_assignment_create", kwargs={"pk": self.cy1.pk})
        )
        self.assertEqual(resp_create.status_code, 404)
        FinalAssignment.objects.create(
            course_semester=self.cy1, title="FA", max_grade=100, due_date=date(2025, 2, 20)
        )
        resp_edit = self.client.get(
            reverse("lms_courses_teacher:final_assignment_edit", kwargs={"pk": self.cy1.pk})
        )
        self.assertEqual(resp_edit.status_code, 404)
