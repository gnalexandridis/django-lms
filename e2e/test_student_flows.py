from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base import E2EBase


class TestStudentNavAndLogout(E2EBase):
    def test_student_nav_and_logout(self):
        self.login_as("s1", "STUDENT")
        self.go("/")
        student_home_links = self.browser.find_elements(By.CSS_SELECTOR, "a[href='/student/']")
        student_courses_links = self.browser.find_elements(
            By.CSS_SELECTOR, "a[href='/student/courses/']"
        )
        teacher_courses_links = self.browser.find_elements(
            By.CSS_SELECTOR, "a[href='/teacher/courses/']"
        )
        assert student_home_links, "Student home link missing"
        assert student_courses_links, "Student courses link missing"
        assert not teacher_courses_links, "Teacher courses link should be hidden for students"
        student_courses_links[0].click()
        self.should_see("Τα μαθήματά μου")

        self.go("/")
        self.click_testid("logout-btn")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='logout-btn']"))
        )


class TestStudentPages(E2EBase):
    def test_student_sees_course_and_details(self):
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
        self.go("/")
        self.click_testid("logout-btn")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='logout-btn']"))
        )

        self.login_as("s1", "STUDENT")
        self.go(self.URL_STUDENT_DASH)
        self.should_see("Πίνακας φοιτητή")
        self.should_see("Programming I")
        self.should_see("Υποβλήθηκε")

        self.should_see("85")
        self.go(self.URL_COURSES_STUDENT)
        course_links = self.browser.find_elements(By.CSS_SELECTOR, "a.block.p-4.border")
        course_links[0].click()
        self.should_see("85")
