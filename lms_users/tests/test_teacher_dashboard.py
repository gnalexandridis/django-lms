import sys
from datetime import date, timedelta
from unittest import mock

from django.core.cache import cache
from django.test import RequestFactory, TestCase

from lms.views.teacher import teacher_export_dashboard, teacher_home
from lms_courses.models import Course, CourseSemester, LabSession
from lms_users.models import Roles, User


class TestTeacherDashboard(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        cache.clear()
        self.teacher = User.objects.create_user("teach_lms", password="x", role=Roles.TEACHER)
        # minimal course + semester for filters
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

    def test_forbidden_for_student(self):
        student = User.objects.create_user("s", password="x", role=Roles.STUDENT)
        self.client.force_login(student)
        resp = self.client.get("/export", {})
        self.assertEqual(resp.status_code, 403)

    def test_export_csv_default_and_header(self):
        req = self.make_request(
            "/export",
            self.teacher,
            {"days": "7", "course": "0"},
        )
        resp = teacher_export_dashboard(req)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])  # type: ignore[index]
        cd = resp["Content-Disposition"]  # type: ignore[index]
        # filename is dashboard_stats_d7_call.csv ("c" + "all")
        self.assertIn("attachment; filename=dashboard_stats_d7_call.csv", cd)

    def test_export_xlsx_with_openpyxl(self):
        class DummyWS:
            title = ""

            def append(self, _row):
                pass

        class DummyWB:
            def __init__(self):
                self.active = DummyWS()

            def create_sheet(self, _name):
                return DummyWS()

            def save(self, _out):
                pass

        class FakeOpenpyxl:
            Workbook = DummyWB

        with (
            mock.patch.dict(sys.modules, {"openpyxl": FakeOpenpyxl()}),
            mock.patch(
                "lms.views.teacher.compute_dashboard_stats",
                return_value={
                    "per_course": [],
                    "active_courses": 0,
                    "unique_students": 0,
                    "upcoming_labs": 0,
                    "lab_grades_done": 0,
                    "lab_grades_null": 0,
                    "fa_submitted": 0,
                    "fa_graded": 0,
                    "fa_avg": None,
                    "overdue_ungraded": 0,
                    "no_attendance_sessions": 0,
                    "attendance_trend": [0, 0, 0],
                },
            ),
        ):
            req = self.make_request(
                "/export",
                self.teacher,
                {"days": "7", "course": str(self.cs.pk), "format": "xlsx"},
            )
            resp = teacher_export_dashboard(req)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resp["Content-Type"],  # type: ignore[index]
            )
            cd = resp["Content-Disposition"]  # type: ignore[index]
            self.assertIn("attachment; filename=dashboard_stats_d7_c", cd)

    def test_export_xlsx_import_error_fallbacks_to_csv(self):
        with mock.patch.dict(sys.modules, {"openpyxl": None}):
            req = self.make_request(
                "/export",
                self.teacher,
                {"days": "7", "course": str(self.cs.pk), "format": "xlsx"},
            )
            resp = teacher_export_dashboard(req)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/csv", resp["Content-Type"])  # type: ignore[index]

    def test_export_xlsx_with_per_course_rows_and_all_courses_filename(self):
        class DummyWS:
            title = ""

            def append(self, _row):
                pass

        class DummyWB:
            def __init__(self):
                self.active = DummyWS()

            def create_sheet(self, _name):
                return DummyWS()

            def save(self, _out):
                pass

        class FakeCourse:
            code = "CSX"
            title = "Course X"

        class FakeCS:
            course = FakeCourse()
            year = 2025
            students_count = 10
            upcoming_sessions = 1
            lab_done = 2
            lab_null = 3
            fa_sub = 4
            fa_grd = 5

        fake_data = {
            "per_course": [FakeCS()],
            "active_courses": 1,
            "unique_students": 10,
            "upcoming_labs": 2,
            "lab_grades_done": 2,
            "lab_grades_null": 3,
            "fa_submitted": 4,
            "fa_graded": 5,
            "fa_avg": 7,
            "overdue_ungraded": 0,
            "no_attendance_sessions": 0,
            "attendance_trend": [1, 2, 3],
        }

        class FakeOpenpyxl:
            Workbook = DummyWB

        with (
            mock.patch.dict(sys.modules, {"openpyxl": FakeOpenpyxl()}),
            mock.patch("lms.views.teacher.compute_dashboard_stats", return_value=fake_data),
        ):
            # Use course=0 to produce the 'all' filename path in XLSX response
            req = self.make_request(
                "/export",
                self.teacher,
                {"days": "14", "course": "0", "format": "xlsx"},
            )
            resp = teacher_export_dashboard(req)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resp["Content-Type"],  # type: ignore[index]
            )
            cd = resp["Content-Disposition"]  # type: ignore[index]
            self.assertIn("attachment; filename=dashboard_stats_d14_call.xlsx", cd)

    def test_export_csv_body_contains_expected_fields(self):
        class FakeCourse:
            code = "CSXYZ"
            title = "Title"

        class FakeCS:
            course = FakeCourse()
            year = 2025
            students_count = 2
            upcoming_sessions = 3
            lab_done = 1
            lab_null = 2
            fa_sub = 1
            fa_grd = 1

        fake_data = {
            "per_course": [FakeCS()],
            "active_courses": 1,
            "unique_students": 2,
            "upcoming_labs": 3,
            "lab_grades_done": 1,
            "lab_grades_null": 2,
            "fa_submitted": 1,
            "fa_graded": 1,
            "fa_avg": 5,
            "overdue_ungraded": 0,
            "no_attendance_sessions": 0,
        }

        with mock.patch("lms.views.teacher.compute_dashboard_stats", return_value=fake_data):
            req = self.make_request(
                "/export",
                self.teacher,
                {"days": "14", "course": str(self.cs.pk), "format": "csv"},
            )
            resp = teacher_export_dashboard(req)
            self.assertEqual(resp.status_code, 200)
            body = resp.content.decode("utf-8-sig")
            self.assertIn("key,value", body)
            self.assertIn("course_code,course_title,year,students", body)
            self.assertIn("CSXYZ,Title,2025,2", body)

    def test_teacher_home_cache_and_invalid_params(self):
        # invalid params path
        req_bad = self.make_request("/teacher/", self.teacher, {"days": "oops", "course": "nope"})
        resp_bad = teacher_home(req_bad)
        self.assertEqual(resp_bad.status_code, 200)

        # cache miss then hit
        req1 = self.make_request(
            "/teacher/",
            self.teacher,
            {"days": "7", "course": str(self.cs.pk)},
        )
        self.assertEqual(teacher_home(req1).status_code, 200)
        req2 = self.make_request(
            "/teacher/",
            self.teacher,
            {"days": "7", "course": str(self.cs.pk)},
        )
        self.assertEqual(teacher_home(req2).status_code, 200)

    def test_teacher_home_days_not_in_options_falls_back_to_7(self):
        req = self.make_request(
            "/teacher/",
            self.teacher,
            {"days": "5", "course": str(self.cs.pk)},
        )
        self.assertEqual(teacher_home(req).status_code, 200)
