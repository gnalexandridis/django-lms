from datetime import date, timedelta

from django.core.cache import cache
from django.test import RequestFactory, TestCase

from lms_courses.models import Course, CourseSemester, LabSession
from lms_users.models import Roles, User


class TestLmsViewsTeacher(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()
        self.teacher = User.objects.create_user("teach_lms", password="x", role=Roles.TEACHER)
        # minimal data for course filter
        c = Course.objects.create(code="CS900", title="LMS T")
        self.cs = CourseSemester.objects.create(
            course=c,
            year=2025,
            semester="WINTER",
            owner=self.teacher,
        )
        LabSession.objects.create(
            name="L1",
            week=1,
            date=date.today() + timedelta(days=2),
            course_semester=self.cs,
        )

    def make_request(self, path, user, params=None):
        req = self.factory.get(path, data=params or {})
        req.user = user  # type: ignore[attr-defined]
        return req
