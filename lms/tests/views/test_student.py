from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from lms_courses.models import (
    Course,
    CourseSemester,
    LabParticipation,
    LabReportGrade,
    LabSession,
)
from lms_users.models import Roles, User


class TestStudentHome(TestCase):
    def setUp(self):
        self.student = User.objects.create_user("stud", password="x", role=Roles.STUDENT)
        self.teacher = User.objects.create_user("teach", password="x", role=Roles.TEACHER)
        self.client.login(username="stud", password="x")
        c = Course.objects.create(code="CSST", title="Student Course")
        self.cs = CourseSemester.objects.create(
            course=c, year=2025, semester="WINTER", owner=self.teacher
        )
        self.cs.students.add(self.student)
        self.sess = LabSession.objects.create(
            name="L1",
            week=1,
            date=date.today() + timedelta(days=1),
            course_semester=self.cs,
        )
        # participation and grade
        LabParticipation.objects.create(session=self.sess, student=self.student, present=True)
        report = getattr(self.sess, "report", None)
        if report:
            LabReportGrade.objects.create(lab_report=report, student=self.student, grade=8)

    def test_student_home_basic(self):
        resp = self.client.get(reverse("student_home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Πίνακας φοιτητή")
        self.assertContains(resp, "Student Course")
        self.assertIn("per_course", resp.context)

    def test_student_home_forbidden_for_teacher(self):
        self.client.logout()
        self.client.login(username="teach", password="x")
        resp = self.client.get(reverse("student_home"))
        self.assertEqual(resp.status_code, 403)

    def test_student_home_forbidden_when_not_student(self):
        User.objects.create_user("t", password="x", role=Roles.TEACHER)
        self.client.login(username="t", password="x")
        resp = self.client.get(reverse("student_home"))
        self.assertEqual(resp.status_code, 403)
