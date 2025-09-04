from django.test import TestCase

from lms_courses.forms import EnrollmentForm
from lms_courses.models import Course, CourseSemester
from lms_users.typing_utils import User


class EnrollmentFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t = User.objects.create_user("teacher", password="x")
        cls.t.role = "TEACHER"
        cls.t.save()
        cls.c = Course.objects.create(code="CS500", title="Algorithms")
        cls.cs = CourseSemester.objects.create(course=cls.c, year=2025, owner=cls.t)

    def _form(self, username: str):
        return EnrollmentForm(data={"username": username}, course_semester=self.cs)

    def test_existing_user_is_enrolled(self):
        s = User.objects.create_user("s1", password="x")
        s.role = "STUDENT"
        s.save()
        f = self._form("s1")
        self.assertTrue(f.is_valid(), f.errors)
        user = f.save()
        self.assertEqual(user.pk, s.pk)
        self.assertTrue(self.cs.students.filter(pk=s.pk).exists())
