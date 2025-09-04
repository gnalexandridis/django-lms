from datetime import date

from django.test import TestCase
from django.urls import reverse

from lms_courses.models import Course, CourseSemester, FinalAssignment, LabSession
from lms_users.typing_utils import User


class DeleteViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = User.objects.create_user("t1", password="x", role="TEACHER")
        cls.t2 = User.objects.create_user("t2", password="x", role="TEACHER")
        cls.s1 = User.objects.create_user("s1", password="x", role="STUDENT")
        cls.c1 = Course.objects.create(code="CS401", title="Programming I")
        cls.cy1 = CourseSemester.objects.create(course=cls.c1, year=2025, owner=cls.t1)
        cls.cy1.students.add(cls.s1)
        cls.session = LabSession.objects.create(
            course_semester=cls.cy1, name="Lab A", week=1, date=date(2025, 1, 7)
        )
        cls.fa = FinalAssignment.objects.create(
            course_semester=cls.cy1, title="FA", max_grade=100, due_date=date(2025, 2, 1)
        )

    def test_owner_can_delete_lab_session(self):
        self.client.login(username="t1", password="x")
        url = reverse(
            "lms_courses_teacher:lab_session_delete",
            kwargs={"pk": self.cy1.pk, "session_id": self.session.pk},
        )
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(LabSession.objects.filter(pk=self.session.pk).exists())

    def test_non_owner_cannot_delete_lab_session(self):
        self.client.login(username="t2", password="x")
        url = reverse(
            "lms_courses_teacher:lab_session_delete",
            kwargs={"pk": self.cy1.pk, "session_id": self.session.pk},
        )
        resp = self.client.post(url)
        # 404 because course-semester doesn't belong to t2
        self.assertEqual(resp.status_code, 404)

    def test_owner_can_delete_final_assignment(self):
        self.client.login(username="t1", password="x")
        url = reverse("lms_courses_teacher:final_assignment_delete", kwargs={"pk": self.cy1.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(FinalAssignment.objects.filter(pk=self.fa.pk).exists())

    def test_owner_can_unenroll_student(self):
        self.client.login(username="t1", password="x")
        url = reverse(
            "lms_courses_teacher:unenroll_student",
            kwargs={"pk": self.cy1.pk, "student_id": self.s1.pk},
        )
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(self.cy1.students.filter(pk=self.s1.pk).exists())

    def test_owner_can_delete_course_semester(self):
        # Create another session to ensure cascading works
        LabSession.objects.create(
            course_semester=self.cy1, name="Lab B", week=2, date=date(2025, 1, 14)
        )
        self.client.login(username="t1", password="x")
        url = reverse("lms_courses_teacher:course_semester_delete", kwargs={"pk": self.cy1.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(CourseSemester.objects.filter(pk=self.cy1.pk).exists())
