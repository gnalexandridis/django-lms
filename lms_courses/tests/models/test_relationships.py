from datetime import date

from django.test import TestCase

from lms_courses.models import Course, CourseSemester, LabSession
from lms_users.typing_utils import User


class RelationshipIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t = User.objects.create_user("t1", password="x")
        cls.c = Course.objects.create(code="CS401", title="Programming I")
        cls.cs = CourseSemester.objects.create(course=cls.c, year=2025, owner=cls.t)

        LabSession.objects.create(
            course_semester=cls.cs, name="Lab A", week=1, date=date(2025, 1, 7)
        )
        LabSession.objects.create(
            course_semester=cls.cs, name="Lab A", week=2, date=date(2025, 1, 14)
        )
        LabSession.objects.create(
            course_semester=cls.cs, name="Lab B", week=1, date=date(2025, 1, 7)
        )

    def test_course_semester_exposes_lab_sessions(self):
        sessions = list(LabSession.objects.filter(course_semester=self.cs))
        self.assertEqual(len(sessions), 3)
        sessions_a = [s for s in sessions if s.name == "Lab A"]
        sessions_b = [s for s in sessions if s.name == "Lab B"]
        self.assertEqual([s.week for s in sessions_a], [1, 2])
        self.assertEqual([s.week for s in sessions_b], [1])

    def test_counts(self):
        sessions = list(LabSession.objects.filter(course_semester=self.cs))
        sessions_a = [s for s in sessions if s.name == "Lab A"]
        sessions_b = [s for s in sessions if s.name == "Lab B"]
        self.assertEqual(len(sessions), 3)
        self.assertEqual(len(sessions_a), 2)
        self.assertEqual(len(sessions_b), 1)
