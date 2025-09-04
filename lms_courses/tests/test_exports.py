from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from lms_courses.models import (
    Course,
    CourseSemester,
    FinalAssignment,
    FinalAssignmentResult,
    LabParticipation,
    LabReportGrade,
    LabSession,
)
from lms_users.models import Roles, User


class TestCourseSemesterExports(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user("teach", password="x", role=Roles.TEACHER)
        self.client.login(username="teach", password="x")
        self.course = Course.objects.create(code="CS200", title="Data")
        self.cs = CourseSemester.objects.create(
            course=self.course,
            year=2025,
            semester="WINTER",
            owner=self.teacher,
        )
        self.s1 = User.objects.create_user("s1", password="x", role=Roles.STUDENT)
        self.s2 = User.objects.create_user("s2", password="x", role=Roles.STUDENT)
        self.cs.students.add(self.s1, self.s2)
        # Sessions + participation + grades
        sess = LabSession.objects.create(
            name="L1",
            week=1,
            date=date.today() + timedelta(days=1),
            course_semester=self.cs,
        )
        LabParticipation.objects.create(session=sess, student=self.s1, present=True)
        LabParticipation.objects.create(session=sess, student=self.s2, present=False)
        # Ensure report auto-created; grade one
        report = getattr(sess, "report", None)
        if report:
            LabReportGrade.objects.create(lab_report=report, student=self.s1, grade=8)
        # Final assignment and results
        fa = FinalAssignment.objects.create(
            title="FA",
            max_grade=10,
            due_date=date.today() + timedelta(days=10),
            course_semester=self.cs,
        )
        FinalAssignmentResult.objects.create(
            final_assignment=fa, student=self.s1, submitted=True, grade=9
        )
        FinalAssignmentResult.objects.create(
            final_assignment=fa, student=self.s2, submitted=False, grade=None
        )

    def test_course_semester_export_csv(self):
        url = (
            reverse("lms_courses_teacher:course_semester_export", kwargs={"pk": self.cs.pk})
            + "?format=csv"
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])  # type: ignore[index]
        body = resp.content.decode("utf-8-sig")
        self.assertIn("course_code,course_title,year,semester", body)
        self.assertIn("CS200", body)
        self.assertIn("sessions: week,name,date,present_count,graded_count".replace(",", ","), body)
        self.assertIn("participations: week,student,present".replace(",", ","), body)
        self.assertIn("lab_grades: week,student,grade".replace(",", ","), body)
        self.assertIn("final_assignment: student,submitted,grade".replace(",", ","), body)

    def test_course_semester_export_xlsx(self):
        url = (
            reverse("lms_courses_teacher:course_semester_export", kwargs={"pk": self.cs.pk})
            + "?format=xlsx"
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            resp["Content-Type"],
        )  # type: ignore[index]
        self.assertGreater(len(resp.content), 100)
        self.assertIn(
            "attachment; filename=course_semester_",
            resp["Content-Disposition"],
        )  # type: ignore[index]
