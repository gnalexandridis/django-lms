from datetime import date

from django.db.utils import IntegrityError
from django.test import TestCase

from lms_courses.models import Course, CourseSemester, LabSession
from lms_users.typing_utils import User


class LabSessionModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t = User.objects.create_user("t1", password="x")
        cls.c = Course.objects.create(code="CS401", title="Programming I")
        cls.cs = CourseSemester.objects.create(
            course=cls.c, year=2025, semester="WINTER", owner=cls.t
        )

    def test_str(self):
        s1 = LabSession.objects.create(
            course_semester=self.cs, name="Lab A", week=1, date=date(2025, 1, 7)
        )
        s = str(s1)
        self.assertIn("Lab A", s)
        self.assertIn("Week 1", s)

    def test_unique_week_per_lab(self):
        LabSession.objects.create(
            course_semester=self.cs, name="Lab A", week=1, date=date(2025, 1, 7)
        )
        with self.assertRaises(IntegrityError):
            LabSession.objects.create(
                course_semester=self.cs, name="Lab A", week=1, date=date(2025, 1, 14)
            )

    def test_same_week_allowed_in_different_lab(self):
        LabSession.objects.create(
            course_semester=self.cs, name="Lab A", week=1, date=date(2025, 1, 7)
        )
        s_other = LabSession.objects.create(
            course_semester=self.cs, name="Lab B", week=1, date=date(2025, 1, 7)
        )
        self.assertIsNotNone(s_other.pk)

    def test_ordering_by_week(self):
        LabSession.objects.create(
            course_semester=self.cs, name="Lab A", week=2, date=date(2025, 1, 14)
        )
        LabSession.objects.create(
            course_semester=self.cs, name="Lab A", week=1, date=date(2025, 1, 7)
        )
        weeks = list(
            LabSession.objects.filter(course_semester=self.cs).values_list("week", flat=True)
        )
        self.assertEqual(weeks, [1, 2])

    def test_cascade_delete_from_course_semester(self):
        s1 = LabSession.objects.create(
            course_semester=self.cs, name="Lab A", week=1, date=date(2025, 1, 7)
        )
        self.cs.delete()
        self.assertFalse(LabSession.objects.filter(pk=s1.pk).exists())

    def test_date_persists(self):
        d = date(2025, 1, 7)
        s = LabSession.objects.create(course_semester=self.cs, name="Lab A", week=1, date=d)
        self.assertEqual(LabSession.objects.get(pk=s.pk).date, d)

    def test_create_lab_session_with_missing_fields(self):
        with self.assertRaises(TypeError):
            LabSession.objects.create(course_semester=self.cs)

    def test_lab_session_week_bounds(self):
        # Negative week
        with self.assertRaises(ValueError):
            LabSession.objects.create(
                course_semester=self.cs,
                name="Lab A",
                week=-1,
                date=date(2025, 1, 7),
            )
        # Zero week
        with self.assertRaises(ValueError):
            LabSession.objects.create(
                course_semester=self.cs,
                name="Lab A",
                week=0,
                date=date(2025, 1, 7),
            )
        # Large week
        s = LabSession.objects.create(
            course_semester=self.cs, name="Lab A", week=52, date=date(2025, 1, 7)
        )
        self.assertEqual(s.week, 52)

    def test_lab_session_date_required(self):
        with self.assertRaises(TypeError):
            LabSession.objects.create(course_semester=self.cs, name="Lab A", week=1)

    def test_lab_session_str_includes_semester(self):
        s = LabSession.objects.create(
            course_semester=self.cs,
            name="Lab A",
            week=1,
            date=date(2025, 1, 7),
        )
        self.assertIn(str(self.cs.year), str(s))
        self.assertIn(self.cs.semester, str(s))
