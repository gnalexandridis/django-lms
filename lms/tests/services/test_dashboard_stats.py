from datetime import date, timedelta

from django.test import TestCase

from lms.services.dashboard import compute_dashboard_stats
from lms_courses.models import (
    Course,
    CourseSemester,
    FinalAssignment,
    LabParticipation,
    LabReportGrade,
    LabSession,
)
from lms_users.models import Roles, User


class TestDashboardStatsComputation(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teach", password="x", role=Roles.TEACHER)
        self.s1 = User.objects.create_user("s1", password="x", role=Roles.STUDENT)
        self.s2 = User.objects.create_user("s2", password="x", role=Roles.STUDENT)

        course1 = Course.objects.create(code="CS300", title="Stats")
        course2 = Course.objects.create(code="CS301", title="More Stats")
        self.cs1 = CourseSemester.objects.create(
            course=course1, year=2025, semester="WINTER", owner=self.teacher
        )
        self.cs2 = CourseSemester.objects.create(
            course=course2, year=2025, semester="SPRING", owner=self.teacher
        )
        self.cs1.students.add(self.s1, self.s2)
        self.cs2.students.add(self.s1)

        # Sessions for cs1
        self.sess_recent = LabSession.objects.create(
            name="L1",
            week=1,
            date=date.today() + timedelta(days=2),
            course_semester=self.cs1,
        )
        # Auto report created, add participations and grades
        LabParticipation.objects.create(session=self.sess_recent, student=self.s1, present=True)
        LabParticipation.objects.create(session=self.sess_recent, student=self.s2, present=False)
        report = getattr(self.sess_recent, "report", None)
        if report:
            LabReportGrade.objects.create(lab_report=report, student=self.s1, grade=7)
            LabReportGrade.objects.create(lab_report=report, student=self.s2, grade=None)

        # Overdue ungraded session (older than 7 days with null grade)
        self.sess_old = LabSession.objects.create(
            name="L0",
            week=3,
            date=date.today() - timedelta(days=10),
            course_semester=self.cs1,
        )
        # Ensure report exists with a null grade to count as overdue_ungraded
        r_old = getattr(self.sess_old, "report", None)
        if r_old:
            LabReportGrade.objects.create(lab_report=r_old, student=self.s1, grade=None)

        # Session with no attendance at all
        self.sess_no_att = LabSession.objects.create(
            name="L2",
            week=2,
            date=date.today() + timedelta(days=3),
            course_semester=self.cs1,
        )

        # Session in other course outside 7 days
        LabSession.objects.create(
            name="Lx",
            week=1,
            date=date.today() + timedelta(days=20),
            course_semester=self.cs2,
        )

        # Final assignment with results
        fa = FinalAssignment.objects.create(
            title="FA",
            max_grade=10,
            due_date=date.today() + timedelta(days=30),
            course_semester=self.cs1,
        )
        fa.results.create(student=self.s1, submitted=True, grade=9)  # type: ignore
        fa.results.create(student=self.s2, submitted=False, grade=None)  # type: ignore

    def test_stats_for_all_courses(self):
        data = compute_dashboard_stats(self.teacher, days=7, selected_course_id=0)
        # Active courses: both cs1 and cs2
        self.assertEqual(data["active_courses"], 2)
        # Unique students across cs1+cs2 should be 2 (s1, s2)
        self.assertEqual(data["unique_students"], 2)
        # Upcoming labs within 7 days: sess_recent and sess_no_att from cs1
        self.assertEqual(data["upcoming_labs"], 2)
        # Lab grades done (exactly one graded)
        self.assertEqual(data["lab_grades_done"], 1)
        # Lab grades null (one null in recent and one null in old)
        self.assertEqual(data["lab_grades_null"], 2)
        # FA submitted and graded counts
        self.assertEqual(data["fa_submitted"], 1)
        self.assertEqual(data["fa_graded"], 1)
        # Overdue ungraded sessions
        self.assertEqual(data["overdue_ungraded"], 1)
        # Sessions with no attendance: includes sessions without any participations
        self.assertEqual(data["no_attendance_sessions"], 3)
        # Trend returns 4 numbers
        self.assertEqual(len(data["attendance_trend"]), 4)
        # Per-course annotations available
        self.assertGreaterEqual(data["per_course"].count(), 2)

    def test_stats_filtered_by_course(self):
        data = compute_dashboard_stats(self.teacher, days=7, selected_course_id=self.cs1.pk)
        # Only cs1 considered
        self.assertEqual(data["active_courses"], 1)
        # Upcoming labs within 7 days: two in cs1
        self.assertEqual(data["upcoming_labs"], 2)
        # Per-course should have exactly one row
        self.assertEqual(data["per_course"].count(), 1)
