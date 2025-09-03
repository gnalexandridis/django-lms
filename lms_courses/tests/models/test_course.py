from django.db.utils import IntegrityError
from django.test import TestCase

from lms_courses.models import Course


class CourseModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.course = Course.objects.create(code="CS401", title="Programming I")

    def test_str(self):
        self.assertEqual(str(self.course), "CS401 — Programming I")

    def test_code_is_unique(self):
        with self.assertRaises(IntegrityError):
            Course.objects.create(code="CS401", title="Duplicate")
