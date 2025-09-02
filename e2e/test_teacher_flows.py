from __future__ import annotations
from .base import E2EBase


class TestCreateCourseSemester(E2EBase):
    def test_teacher_creates_course_semester(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )
