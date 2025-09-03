from typing import cast

from django.forms import ModelChoiceField
from django.test import RequestFactory, TestCase

from lms_courses.forms import CourseSemesterForm
from lms_courses.models import Course, CourseSemester
from lms_users.typing_utils import User


class CourseSemesterFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rf = RequestFactory()
        cls.t1 = User.objects.create_user("t1", password="x", email="t1@example.com")
        cls.t2 = User.objects.create_user("t2", password="x", email="t2@example.com")
        cls.c1 = Course.objects.create(code="CS401", title="Programming I")
        cls.c2 = Course.objects.create(code="CS402", title="Programming II")

    def _req_as(self, user):
        req = self.rf.post("/fake/")
        req.user = user
        return req

    def test_form_renders_course_and_year_fields(self):
        form = CourseSemesterForm(request=self._req_as(self.t1))
        self.assertIn('name="course"', str(form))
        self.assertIn('name="year"', str(form))
        self.assertIn('name="semester"', str(form))
        self.assertIn('name="enrollment_limit"', str(form))

    def test_valid_form_sets_owner_and_saves(self):
        data = {"course": self.c1.pk, "year": 2025, "semester": "WINTER", "enrollment_limit": 30}
        form = CourseSemesterForm(data=data, request=self._req_as(self.t1))
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.owner, self.t1)
        self.assertEqual(instance.course, self.c1)
        self.assertEqual(instance.year, 2025)
        self.assertEqual(instance.semester, "WINTER")
        self.assertEqual(instance.enrollment_limit, 30)

    def test_duplicate_same_owner_course_year_is_rejected(self):
        CourseSemester.objects.create(course=self.c1, year=2025, owner=self.t1)
        data = {"course": self.c1.pk, "year": 2025, "semester": "WINTER", "enrollment_limit": 30}
        form = CourseSemesterForm(data=data, request=self._req_as(self.t1))
        self.assertFalse(form.is_valid())
        self.assertIn("already exists", str(form.errors))

    def test_same_course_year_allowed_for_other_owner(self):
        CourseSemester.objects.create(course=self.c1, year=2025, owner=self.t2)
        data = {"course": self.c1.pk, "year": 2025, "semester": "WINTER", "enrollment_limit": 30}
        form = CourseSemesterForm(data=data, request=self._req_as(self.t1))
        self.assertTrue(form.is_valid(), form.errors)

    def test_year_bounds(self):
        # κάτω από 2000
        form = CourseSemesterForm(
            data={"course": self.c1.pk, "year": 1999, "semester": "WINTER", "enrollment_limit": 30},
            request=self._req_as(self.t1),
        )
        self.assertFalse(form.is_valid())
        # πάνω από 2100
        form = CourseSemesterForm(
            data={"course": self.c1.pk, "year": 2101, "semester": "WINTER", "enrollment_limit": 30},
            request=self._req_as(self.t1),
        )
        self.assertFalse(form.is_valid())
        # οκ
        form = CourseSemesterForm(
            data={"course": self.c1.pk, "year": 2000, "semester": "WINTER", "enrollment_limit": 30},
            request=self._req_as(self.t1),
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_course_queryset_is_catalog(self):
        form = CourseSemesterForm(request=self._req_as(self.t1))
        course_field = cast(ModelChoiceField, form.fields["course"])
        qs = list(course_field.queryset)
        self.assertIn(self.c1, qs)
        self.assertIn(self.c2, qs)

    def test_invalid_semester_choice(self):
        data = {"course": self.c1.pk, "year": 2025, "semester": "SUMMER", "enrollment_limit": 30}
        form = CourseSemesterForm(data=data, request=self._req_as(self.t1))
        self.assertFalse(form.is_valid())
        self.assertIn("Select a valid choice", str(form.errors))

    def test_missing_required_fields(self):
        data = {"course": self.c1.pk}
        form = CourseSemesterForm(data=data, request=self._req_as(self.t1))
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required", str(form.errors))

    def test_enrollment_limit_optional(self):
        data = {"course": self.c1.pk, "year": 2025, "semester": "WINTER"}
        form = CourseSemesterForm(data=data, request=self._req_as(self.t1))
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertIsNone(instance.enrollment_limit)
