from __future__ import annotations
from .base import E2EBase


class TestCreateCourseSemester(E2EBase):
    def test_teacher_creates_course_semester(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )


class TestCreateLabsAndSessions(E2EBase):
    def test_teacher_adds_lab_and_sessions(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )
        self.teacher_adds_lab_session(
            course_title="Programming I",
            course_year=2025,
            course_semester="Χειμερινό",
            lab_name="Lab A",
            week=1,
            date_iso="2025-01-07",
        )
        self.teacher_adds_lab_session(
            course_title="Programming I",
            course_year=2025,
            course_semester="Χειμερινό",
            lab_name="Lab A",
            week=2,
            date_iso="2025-01-14",
        )
