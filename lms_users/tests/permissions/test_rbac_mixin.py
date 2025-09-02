from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import path, reverse
from django.views import View

from lms_users.permissions import RoleRequiredMixin, Roles
from lms_users.typing_utils import UserModel as U


class RBACView(RoleRequiredMixin, View):
    allowed_roles = (Roles.TEACHER,)

    def get(self, request):
        return HttpResponse("ok")


class RBACAnyLoggedInView(RoleRequiredMixin, View):
    allowed_roles = None  # allow any authenticated user

    def get(self, request):
        return HttpResponse("ok-any")


urlpatterns = [
    path("rbac/", RBACView.as_view(), name="rbac_view"),
    path("rbac-any/", RBACAnyLoggedInView.as_view(), name="rbac_any_view"),
]


@override_settings(ROOT_URLCONF=__name__)
class RoleRequiredMixinTests(TestCase):
    def setUp(self):
        self.teacher = U.objects.create_user("t1", password="x")
        self.teacher.role = "TEACHER"
        self.teacher.save()

        self.student = U.objects.create_user("s1", password="x")
        self.student.role = "STUDENT"
        self.student.save()

        self.staff_user = U.objects.create_user("st1", password="x")
        self.staff_user.role = "STUDENT"
        self.staff_user.is_staff = True
        self.staff_user.save()

        self.super_user = U.objects.create_superuser("su", email="su@example.com", password="x")

    def test_teacher_allowed(self):
        self.client.login(username="t1", password="x")
        r = self.client.get(reverse("rbac_view"))
        self.assertEqual(r.status_code, 200)

    def test_student_forbidden(self):
        self.client.login(username="s1", password="x")
        r = self.client.get(reverse("rbac_view"))
        self.assertEqual(r.status_code, 403)

    def test_staff_bypass_allowed(self):
        self.client.login(username="st1", password="x")
        r = self.client.get(reverse("rbac_view"))
        self.assertEqual(r.status_code, 200)

    def test_superuser_bypass_allowed(self):
        self.client.login(username="su", password="x")
        r = self.client.get(reverse("rbac_view"))
        self.assertEqual(r.status_code, 200)

    def test_any_logged_in_allowed_when_roles_none(self):
        self.client.login(username="s1", password="x")
        r = self.client.get(reverse("rbac_any_view"))
        self.assertEqual(r.status_code, 200)
