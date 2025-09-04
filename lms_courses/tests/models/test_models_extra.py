from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from lms_courses.models import (
    Course,
    CourseSemester,
    FinalAssignment,
    LabReport,
    LabReportGrade,
    LabSession,
)


class TestModelCountersAndStr(TestCase):
    def setUp(self):
        U = get_user_model()
        self.teacher = U.objects.create_user(username="t", role="TEACHER")
        self.student = U.objects.create_user(username="s", role="STUDENT")
        self.course = Course.objects.create(code="CS1", title="T1")
        self.cs = CourseSemester.objects.create(
            course=self.course, year=2025, semester="WINTER", owner=self.teacher
        )
        self.session = LabSession.objects.create(
            name="L1", week=1, date=date(2025, 1, 10), course_semester=self.cs
        )

    def test_present_and_graded_counts_and_str(self):
        # Ensure LabReport auto-created
        report = LabReport.objects.get(session=self.session)
        self.assertIsNotNone(report)
        # Initially zero
        self.assertEqual(self.session.present_count, 0)
        self.assertEqual(self.session.graded_count, 0)
        # Add a grade
        LabReportGrade.objects.create(lab_report=report, student=self.student, grade=9)
        self.assertEqual(self.session.graded_count, 1)
        # __str__ are defined
        str(self.cs)
        str(self.session)
        str(report)

    def test_final_assignment_counters(self):
        fa = FinalAssignment.objects.create(
            title="F", max_grade=100, due_date=date(2025, 2, 1), course_semester=self.cs
        )
        # Initially zero
        self.assertEqual(fa.submitted_count, 0)
        self.assertEqual(fa.graded_count, 0)
