from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base import E2EBase


class TestCreateCourseYear(E2EBase):
    def test_teacher_creates_course_year(self):
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


class TestEnrollStudent(E2EBase):
    def test_teacher_enrolls_student(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )
        self.teacher_enroll_student(
            course_title="Programming I", course_year=2025, student_username="s1"
        )


class TestFinalAssignmentCreate(E2EBase):
    def test_teacher_creates_final_assignment(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )
        self.teacher_creates_final_assignment(
            course_title="Programming I",
            course_year=2025,
            course_semester="Χειμερινό",
            title="Final Assignment",
            max_grade=100,
            due_date_iso="2025-02-20",
        )


class TestFinalAssignmentManage(E2EBase):
    def test_teacher_manages_final_assignment(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )
        self.teacher_enroll_student(
            course_title="Programming I", course_year=2025, student_username="s1"
        )
        self.teacher_creates_final_assignment(
            course_title="Programming I",
            course_year=2025,
            course_semester="Χειμερινό",
            title="Final Assignment",
            max_grade=100,
            due_date_iso="2025-02-20",
        )
        self.teacher_manages_final_assignment_results(
            course_title="Programming I", course_year=2025, submitted=True, grade=85
        )


class TestLabParticipationAndGrades(E2EBase):
    def test_teacher_marks_participation_and_grades(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )
        self.teacher_enroll_student(
            course_title="Programming I", course_year=2025, student_username="s1"
        )
        self.teacher_adds_lab_session(
            course_title="Programming I",
            course_year=2025,
            course_semester="Χειμερινό",
            lab_name="Lab A",
            week=1,
            date_iso="2025-01-07",
        )
        self.teacher_marks_participation_and_grades(
            course_title="Programming I",
            course_year=2025,
            session_week=1,
            student_username="s1",
            present=True,
            grade=8,
        )


class TestDashboardFiltersAndExports(E2EBase):
    def test_teacher_dashboard_filters_and_exports(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )

        self.go("/")
        self.select_by_visible_text("days", "7")
        self.click_testid("apply-dashboard-filters")
        self.should_see("σε 7 ημ.")

        self.select_by_visible_text("course", "CS401 — Programming I @ 2025")
        self.click_testid("apply-dashboard-filters")
        self.should_see("Programming I")

        for testid, fmt in (("export-dashboard-csv", "csv"), ("export-dashboard-xlsx", "xlsx")):
            link = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{testid}']"))
            )
            href = link.get_attribute("href") or ""
            assert ("format=" + fmt) in href and "days=" in href

        self.go(self.URL_COURSES_TEACHER)
        table = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="course-semesters-table"]')
            )
        )
        row = table.find_element(By.CSS_SELECTOR, "tr[data-code='CS401'][data-year='2025']")
        row.find_element(By.CSS_SELECTOR, '[data-testid="col-title"]').click()
        for testid, fmt in (
            ("export-course-semester-csv", "csv"),
            ("export-course-semester-xlsx", "xlsx"),
        ):
            link = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='{testid}']"))
            )
            href = link.get_attribute("href") or ""
            assert ("format=" + fmt) in href


class TestDeleteFlows(E2EBase):
    def test_teacher_can_delete_entities(self):
        self.login_as("t1", "TEACHER")
        self.teacher_creates_course_semester_from_list(
            course_title="Programming I", course_year=2025, course_semester="Χειμερινό"
        )
        self.teacher_enroll_student(
            course_title="Programming I", course_year=2025, student_username="s1"
        )
        self.teacher_adds_lab_session(
            course_title="Programming I",
            course_year=2025,
            course_semester="Χειμερινό",
            lab_name="Lab A",
            week=1,
            date_iso="2025-01-07",
        )
        self.teacher_creates_final_assignment(
            course_title="Programming I",
            course_year=2025,
            course_semester="Χειμερινό",
            title="Final Assignment",
            max_grade=100,
            due_date_iso="2025-02-20",
        )
        # Delete lab session and final assignment, unenroll student, then delete course-semester
        self.teacher_deletes_first_lab_session("Programming I", 2025)
        self.teacher_deletes_final_assignment("Programming I", 2025)
        self.teacher_unenroll_first_student("Programming I", 2025)
        self.teacher_deletes_course_semester("Programming I", 2025)
