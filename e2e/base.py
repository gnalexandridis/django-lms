from __future__ import annotations

from typing import ClassVar

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from lms_courses.models import Course

TIMEOUT = 10


@override_settings(E2E_TEST_LOGIN=True)
class E2EBase(StaticLiveServerTestCase):
    """
    Base with helpers + one Chrome instance.
    All tests assume an in-app '/users/test-login/' form exists.
    Every test is independent and creates what it needs via UI.
    """

    # These are set in setUpClass; declared here for type-checkers
    browser: ClassVar[webdriver.Chrome]
    wait: ClassVar[WebDriverWait]

    # ---- URLs used across flows (adapt names if your urls.py differs) ----
    URL_LOGIN = "/users/test-login/"
    URL_TEACHER_DASH = "/teacher/"  # teacher home (optional; used in helpers)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")  # enable for CI
        options.add_argument("--window-size=1280,1024")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        cls.browser = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.browser, TIMEOUT)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.browser.quit()
        finally:
            super().tearDownClass()

    def setUp(self):
        super().setUp()

    # ---- tiny utilities ---------------------------------------------------
    def go(self, path: str):
        self.browser.get(self.live_server_url + path)
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    def click_testid(self, testid: str):
        self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'[data-testid="{testid}"]'))
        ).click()

    def fill_by_name(self, name: str, value: str):
        el = self.wait.until(EC.presence_of_element_located((By.NAME, name)))
        el.clear()
        el.send_keys(value)

    def select_by_visible_text(self, name: str, visible_text: str):
        el = self.wait.until(EC.presence_of_element_located((By.NAME, name)))
        Select(el).select_by_visible_text(visible_text)

    def should_see(self, text: str):
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))

    def accept_confirm_alert(self, expected_substring: str | None = None):
        """Wait for a JS alert/confirm, optionally assert text, then accept it.

        - expected_substring: if provided, must be contained in the alert text.
        """
        try:
            alert = self.wait.until(EC.alert_is_present())
        except Exception:
            return  # nothing to do
        text = alert.text or ""
        if expected_substring and expected_substring not in text:
            raise AssertionError(f"Alert missing '{expected_substring}'; got: '{text}'")
        alert.accept()
        # ensure it's gone before continuing
        try:
            WebDriverWait(self.browser, 2).until_not(EC.alert_is_present())
        except Exception:
            pass

    # ---- common flow helpers ----------------------------------------------
    def login_as(self, username: str, role: str, password: str = "x"):
        # Start from index and click the Login link (role-agnostic, respects LOGIN_LINK)
        self.go("/")
        # Check that the user is automatically redirected to the test login page
        self.wait.until(EC.url_contains("/users/test-login/"))
        self.fill_by_name("username", username)
        self.fill_by_name("password", password)
        role_elems = self.browser.find_elements(By.NAME, "role")
        if role_elems:
            el = role_elems[0]
            if el.tag_name.lower() == "select":
                Select(el).select_by_value(role)
            else:
                el.clear()
                el.send_keys(role)
        self.browser.find_element(By.CSS_SELECTOR, "button[type=submit],input[type=submit]").click()
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Sanity: after login, user should land on their role-based home
        if role == "TEACHER":
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/teacher/courses/']"))
            )
        elif role == "STUDENT":
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/student/courses/']"))
            )

    def teacher_creates_course_semester_from_list(
        self, course_title: str, course_year: int, course_semester: str
    ):
        # Navigate like a real user: from home, click the courses link
        self.go("/")
        self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/teacher/courses/']"))
        ).click()
        self.click_testid("create-course-semester")
        self.select_by_visible_text("course", course_title)
        self.fill_by_name("year", str(course_year))
        self.select_by_visible_text("semester", course_semester)
        self.fill_by_name("enrollment_limit", "30")
        self.click_testid("submit-course-semester")

        table = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="course-semesters-table"]')
            )
        )
        code = Course.objects.get(title=course_title).code
        row = table.find_element(
            By.CSS_SELECTOR, f'tr[data-code="{code}"][data-year="{course_year}"]'
        )
        assert course_title in row.find_element(By.CSS_SELECTOR, '[data-testid="col-title"]').text
