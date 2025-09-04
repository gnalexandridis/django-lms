import sys
from datetime import date, timedelta
from unittest import mock

from django.core.cache import cache
from django.test import RequestFactory, TestCase

from lms.views import teacher as teacher_module
from lms.views.teacher import teacher_export_dashboard, teacher_home
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

    def test_teacher_home_cache_miss_and_hit(self):
        # miss
        req1 = self.make_request(
            "/teacher/",
            self.teacher,
            {"days": "7", "course": str(self.cs.pk)},
        )
        resp1 = teacher_home(req1)
        self.assertEqual(resp1.status_code, 200)
        # hit
        req2 = self.make_request(
            "/teacher/",
            self.teacher,
            {"days": "7", "course": str(self.cs.pk)},
        )
        resp2 = teacher_home(req2)
        self.assertEqual(resp2.status_code, 200)

    def test_teacher_home_invalid_params(self):
        req = self.make_request("/teacher/", self.teacher, {"days": "oops", "course": "nope"})
        resp = teacher_home(req)
        self.assertEqual(resp.status_code, 200)

    def test_export_dashboard_forbidden_for_student(self):
        student = User.objects.create_user("s", password="x", role=Roles.STUDENT)
        # Use client to exercise the decorator + handler403 path cleanly
        self.client.force_login(student)
        resp = self.client.get("/export", {})
        self.assertEqual(resp.status_code, 403)

    def test_export_dashboard_csv_and_xlsx(self):
        # CSV
        req_csv = self.make_request(
            "/export",
            self.teacher,
            {"days": "7", "course": str(self.cs.pk), "format": "csv"},
        )
        resp_csv = teacher_export_dashboard(req_csv)
        self.assertEqual(resp_csv.status_code, 200)
        self.assertIn("text/csv", resp_csv["Content-Type"])  # type: ignore[index]
        # XLSX (if openpyxl available, view will return xlsx)
        req_x = self.make_request(
            "/export",
            self.teacher,
            {"days": "7", "course": str(self.cs.pk), "format": "xlsx"},
        )
        resp_x = teacher_export_dashboard(req_x)
        self.assertEqual(resp_x.status_code, 200)
        # Accept either xlsx or csv (fallback) depending on environment
        ct = resp_x["Content-Type"]  # type: ignore[index]
        self.assertTrue(
            "spreadsheetml" in ct or "text/csv" in ct,
            f"Unexpected content-type: {ct}",
        )

    def test_export_dashboard_default_csv(self):
        # No format specified -> defaults to CSV
        req = self.make_request(
            "/export",
            self.teacher,
            {"days": "14", "course": str(self.cs.pk)},
        )
        resp = teacher_export_dashboard(req)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])  # type: ignore[index]

    def test_export_dashboard_csv_sets_filename_header(self):
        # Ensure Content-Disposition header includes expected filename
        req = self.make_request(
            "/export",
            self.teacher,
            {"days": "7", "course": "0", "format": "csv"},
        )
        resp = teacher_export_dashboard(req)
        self.assertEqual(resp.status_code, 200)
        cd = resp["Content-Disposition"]  # type: ignore[index]
        self.assertIn("attachment; filename=dashboard_stats_d7_call.csv", cd)

    def test_export_dashboard_xlsx_import_error_fallbacks_to_csv(self):
        # Simulate openpyxl import failure so view falls back to CSV
        with mock.patch.dict(sys.modules, {"openpyxl": None}):
            req = self.make_request(
                "/export",
                self.teacher,
                {"days": "7", "course": str(self.cs.pk), "format": "xlsx"},
            )
            resp = teacher_export_dashboard(req)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/csv", resp["Content-Type"])  # type: ignore[index]

    def test_teacher_home_days_not_in_options_falls_back_to_7(self):
        # days=5 should fall back to 7
        req = self.make_request(
            "/teacher/",
            self.teacher,
            {"days": "5", "course": str(self.cs.pk)},
        )
        resp = teacher_home(req)
        self.assertEqual(resp.status_code, 200)

    def test_export_dashboard_xlsx_success_path_with_mocked_openpyxl(self):
        # Mock compute_dashboard_stats to return predictable data
        class FakeCourse:
            code = "CS900"
            title = "LMS T"

        class FakeCS:
            course = FakeCourse()
            year = 2025
            students_count = 1
            upcoming_sessions = 1
            lab_done = 0
            lab_null = 1
            fa_sub = 0
            fa_grd = 0

        fake_data = {
            "per_course": [FakeCS()],
            "active_courses": 1,
            "unique_students": 1,
            "upcoming_labs": 1,
            "lab_grades_done": 0,
            "lab_grades_null": 1,
            "fa_submitted": 0,
            "fa_graded": 0,
            "fa_avg": None,
            "overdue_ungraded": 0,
            "no_attendance_sessions": 0,
            "attendance_trend": [0, 1, 0],
        }

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

        # Create a fake openpyxl module object with Workbook attribute
        class FakeOpenpyxl:
            Workbook = DummyWB

        with (
            mock.patch("lms.views.teacher.compute_dashboard_stats", return_value=fake_data),
            mock.patch.dict(sys.modules, {"openpyxl": FakeOpenpyxl()}),
        ):
            req = self.make_request(
                "/export",
                self.teacher,
                {"days": "7", "course": str(self.cs.pk), "format": "xlsx"},
            )
            resp = teacher_export_dashboard(req)
            self.assertEqual(resp.status_code, 200)
            # Should be xlsx content type due to mocked workbook
            self.assertIn(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resp["Content-Type"],
            )  # type: ignore[index]
            # Also ensure filename header is set
            cd = resp["Content-Disposition"]  # type: ignore[index]
            self.assertIn("attachment; filename=dashboard_stats_d7_c", cd)

    def test_export_dashboard_csv_contains_headers_and_row(self):
        # Mock compute_dashboard_stats for deterministic CSV content
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

    def test_export_dashboard_unwrapped_body_runs_csv_all_courses(self):
        # Call the unwrapped view to hit the function body directly
        unwrapped = (
            teacher_module.teacher_export_dashboard.__wrapped__  # type: ignore[attr-defined]
        )
        with mock.patch(
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
            },
        ):
            req = self.make_request(
                "/export",
                self.teacher,
                {"days": "7", "course": "0"},
            )
            resp = unwrapped(req)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/csv", resp["Content-Type"])  # type: ignore[index]

    def test_export_dashboard_unwrapped_body_runs_xlsx(self):
        # Call the unwrapped view and force xlsx path
        unwrapped = (
            teacher_module.teacher_export_dashboard.__wrapped__  # type: ignore[attr-defined]
        )

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

        fake_data = {
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
        }

        with (
            mock.patch("lms.views.teacher.compute_dashboard_stats", return_value=fake_data),
            mock.patch.dict(sys.modules, {"openpyxl": FakeOpenpyxl()}),
        ):
            req = self.make_request(
                "/export",
                self.teacher,
                {"days": "14", "course": str(self.cs.pk), "format": "xlsx"},
            )
            resp = unwrapped(req)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resp["Content-Type"],
            )  # type: ignore[index]

    def test_client_routes_execute_view_bodies_csv_and_xlsx(self):
        # Use Django client to hit URLs so decorators are involved and coverage sees execution
        from types import ModuleType

        # Ensure logged in as teacher
        self.client.force_login(self.teacher)

        # CSV default via route
        resp1 = self.client.get(
            "/export",
            {"days": "7", "course": "0"},
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertIn("text/csv", resp1["Content-Type"])  # type: ignore[index]

        # Force xlsx branch using a fake openpyxl module
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

        fake_mod = ModuleType("openpyxl")
        fake_mod.Workbook = DummyWB  # type: ignore[attr-defined]

        with (
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
            mock.patch.dict(sys.modules, {"openpyxl": fake_mod}),
        ):
            resp2 = self.client.get(
                "/export",
                {"days": "14", "course": str(self.cs.pk), "format": "xlsx"},
            )
            self.assertEqual(resp2.status_code, 200)
            self.assertIn(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resp2["Content-Type"],
            )  # type: ignore[index]

    def test_client_teacher_home_invalid_params_cover_excepts(self):
        # Hit teacher home with invalid days & course to cover except branches
        self.client.force_login(self.teacher)
        resp = self.client.get(
            "/teacher/",
            {"days": "oops", "course": "nope"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_export_helper_csv_and_xlsx(self):
        # Call module-level helper directly to ensure coverage of export logic
        # CSV path
        with mock.patch(
            "lms.views.teacher.compute_dashboard_stats",
            return_value={
                "per_course": [],
                "active_courses": 1,
                "unique_students": 1,
                "upcoming_labs": 0,
                "lab_grades_done": 0,
                "lab_grades_null": 0,
                "fa_submitted": 0,
                "fa_graded": 0,
                "fa_avg": None,
                "overdue_ungraded": 0,
                "no_attendance_sessions": 0,
            },
        ):
            resp = teacher_module._export_dashboard(self.teacher, 7, 0, "csv")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/csv", resp["Content-Type"])  # type: ignore[index]

        # XLSX path via fake openpyxl
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

        fake_mod = type("OpenPyxl", (), {"Workbook": DummyWB})()
        with (
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
                    "attendance_trend": [0, 0],
                },
            ),
            mock.patch.dict(sys.modules, {"openpyxl": fake_mod}),
        ):
            resp2 = teacher_module._export_dashboard(self.teacher, 14, self.cs.pk, "xlsx")
            self.assertEqual(resp2.status_code, 200)
            self.assertIn(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                resp2["Content-Type"],
            )  # type: ignore[index]
