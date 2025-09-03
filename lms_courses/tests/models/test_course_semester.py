from django.db.utils import IntegrityError
from django.test import TestCase

from lms_courses.models import Course, CourseSemester
from lms_users.typing_utils import User


class CourseSemesterModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = User.objects.create_user("t1", password="x", email="t1@example.com")
        cls.t2 = User.objects.create_user("t2", password="x", email="t2@example.com")
        cls.c1 = Course.objects.create(code="CS401", title="Programming I")
        cls.c2 = Course.objects.create(code="CS402", title="Programming II")

    def test_str(self):
        cs = CourseSemester.objects.create(
            course=self.c1, year=2025, semester="WINTER", owner=self.t1
        )
        s = str(cs)
        self.assertIn("CS401", s)
        self.assertIn("2025", s)
        self.assertIn("t1", s)
        self.assertIn("WINTER", s)

    def test_unique_per_owner_course_semester(self):
        """Δεν επιτρέπεται διπλό (course, year, semester) για τον ίδιο owner."""
        CourseSemester.objects.create(course=self.c1, year=2025, semester="WINTER", owner=self.t1)
        with self.assertRaises(IntegrityError):
            CourseSemester.objects.create(
                course=self.c1, year=2025, semester="WINTER", owner=self.t1
            )

    def test_same_course_semester_allowed_for_different_owners(self):
        """Επιτρέπεται ίδιο (course, year, semester) για διαφορετικούς owners."""
        cy1 = CourseSemester.objects.create(
            course=self.c1, year=2025, semester="WINTER", owner=self.t1
        )
        cy2 = CourseSemester.objects.create(
            course=self.c1, year=2025, semester="WINTER", owner=self.t2
        )
        self.assertNotEqual(cy1.pk, cy2.pk)

    def test_ordering_latest_year_first_then_course_code(self):
        """
        Περιμένουμε ταξινόμηση:
        - Πρώτα μεγαλύτερο έτος (desc)
        - Για ίδιο έτος, αύξουσα κατά course.code
        """
        CourseSemester.objects.create(course=self.c1, year=2024, semester="WINTER", owner=self.t1)
        CourseSemester.objects.create(
            course=self.c2, year=2025, semester="WINTER", owner=self.t1
        )  # CS402
        CourseSemester.objects.create(
            course=self.c1, year=2025, semester="WINTER", owner=self.t1
        )  # CS401

        qs = list(CourseSemester.objects.all())
        # Αναμενόμενη σειρά: (2025, CS401), (2025, CS402), (2024, CS401)
        self.assertEqual(qs[0].year, 2025)
        self.assertEqual(qs[1].year, 2025)
        self.assertEqual(qs[2].year, 2024)
        self.assertEqual(qs[0].course.code, "CS401")
        self.assertEqual(qs[1].course.code, "CS402")
        self.assertEqual(qs[2].course.code, "CS401")

    def test_cascade_delete_when_course_deleted(self):
        cs = CourseSemester.objects.create(course=self.c1, year=2025, owner=self.t1)
        self.c1.delete()
        self.assertFalse(CourseSemester.objects.filter(pk=cs.pk).exists())

    def test_cascade_delete_when_owner_deleted(self):
        cs = CourseSemester.objects.create(course=self.c1, year=2025, owner=self.t1)
        self.t1.delete()
        self.assertFalse(CourseSemester.objects.filter(pk=cs.pk).exists())
