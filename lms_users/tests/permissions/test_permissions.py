from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import path, reverse

# Import will fail initially - good (Red), write the decorator in the app afterwards.
from lms_users.decorators import role_required
from lms_users.typing_utils import UserModel as U


def teacher_only_view(request):
    return HttpResponse("ok")


urlpatterns = [
    path("teacher-area/", role_required("TEACHER")(teacher_only_view), name="teacher_area"),
]


@override_settings(ROOT_URLCONF=__name__)
class RoleRequiredTests(TestCase):
    def setUp(self):
        self.teacher = U.objects.create_user(username="t1", password="x", email="t1@example.com")
        self.teacher.role = "TEACHER"
        self.teacher.save()
        self.student = U.objects.create_user(username="s1", password="x", email="s1@example.com")
        self.student.role = "STUDENT"
        self.student.save()

    def test_teacher_can_access(self):
        self.client.login(username="t1", password="x")
        r = self.client.get(reverse("teacher_area"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "ok")

    def test_student_gets_403(self):
        self.client.login(username="s1", password="x")
        r = self.client.get(reverse("teacher_area"))
        self.assertEqual(r.status_code, 403)
