from django.http import Http404, HttpResponse
from django.test import RequestFactory, TestCase
from django.views import View

from lms_users.models import Roles, User
from lms_users.permissions import OwnerRequiredMixin, RoleRequiredMixin


class DummyRoleView(RoleRequiredMixin, View):
    allowed_roles = (Roles.TEACHER,)

    def get(self, request):  # type: ignore[override]
        return HttpResponse("ok")


class DummyModel:
    _default_manager = User._default_manager  # reuse User manager for simplicity


class DummyOwnerView(OwnerRequiredMixin, View):
    allowed_roles = (Roles.TEACHER,)
    model = DummyModel
    owner_field = "role"  # not real, just to exercise code path safely

    def get_owned_queryset(self):  # override to return a queryset with always false filter
        return User.objects.none()

    def get(self, request):  # type: ignore[override]
        return HttpResponse("ok")


class TestPermissionMixins(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user("t", password="x", role=Roles.TEACHER)

    def test_role_required_mixin_allows(self):
        req = self.factory.get("/")
        req.user = self.user  # type: ignore[attr-defined]
        resp = DummyRoleView.as_view()(req)
        self.assertEqual(resp.status_code, 200)

    def test_owner_required_mixin_404_when_not_found(self):
        req = self.factory.get("/")
        req.user = self.user  # type: ignore[attr-defined]
        with self.assertRaises(Http404):
            # Http404 raised by get_object_or_404 when object not found
            DummyOwnerView.as_view()(req, pk=1)
