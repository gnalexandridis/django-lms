from django.contrib.admin.sites import site as admin_site
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from lms_courses.models import (
    Course,
    CourseSemester,
    FinalAssignment,
    FinalAssignmentResult,
    LabParticipation,
    LabReport,
    LabReportGrade,
    LabSession,
)


class CoursesAdminRegistrationTests(TestCase):
    def test_models_registered_in_admin(self):
        for model in [
            Course,
            CourseSemester,
            LabSession,
            LabReport,
            LabParticipation,
            LabReportGrade,
            FinalAssignment,
            FinalAssignmentResult,
        ]:
            self.assertIn(model, admin_site._registry)

    def test_changelists_load_for_superuser(self):
        U = get_user_model()
        admin_user = U.objects.create_superuser(
            username="admin", password="x", email="admin@example.com"
        )
        self.client.force_login(admin_user)

        for model in [
            Course,
            CourseSemester,
            LabSession,
            LabReport,
            LabParticipation,
            LabReportGrade,
            FinalAssignment,
            FinalAssignmentResult,
        ]:
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            url = reverse(f"admin:{app_label}_{model_name}_changelist")
            r = self.client.get(url)
            self.assertEqual(
                r.status_code,
                200,
                msg=f"Failed to load admin changelist for {app_label}.{model_name}",
            )
