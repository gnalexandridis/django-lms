from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    ListView,
    TemplateView,
)
from django.urls import reverse_lazy

from lms_users.permissions import OwnerRequiredMixin, RoleRequiredMixin, Roles

from ..models import (
    CourseSemester,
)

from ..forms import (
    CourseSemesterForm,
)


@method_decorator(login_required, name="dispatch")
class MyCourseSemestersList(RoleRequiredMixin, ListView):
    template_name = "lms_courses/teacher/my_course_semesters.html"
    context_object_name = "course_semesters"
    allowed_roles = (Roles.TEACHER,)

    def get_queryset(self):
        return CourseSemester.objects.select_related("course").filter(owner=self.request.user)


@method_decorator(login_required, name="dispatch")
class CourseSemesterCreate(RoleRequiredMixin, CreateView):
    template_name = "lms_courses/teacher/course_semester_create.html"
    form_class = CourseSemesterForm
    success_url = reverse_lazy("lms_courses_teacher:course_semester_list_teacher")
    allowed_roles = (Roles.TEACHER,)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class CourseSemesterDetailView(OwnerRequiredMixin, TemplateView):
    template_name = "lms_courses/teacher/course_semester_detail.html"
    allowed_roles = (Roles.TEACHER,)
    model = CourseSemester

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cs = self.object  # type: ignore[attr-defined]
        # Prefetch sessions for all lab sessions (λιγότερα queries + σιγουριά ότι φαίνονται αμέσως)
        sessions = cs.sessions.all()  # type: ignore[attr-defined]
        ctx["course_semester"] = cs
        ctx["sessions"] = sessions
        ctx["students"] = cs.students.all()
        # Provide final_assignment (if implemented as a OneToOne with related_name).
        # Falls back to None so template shows the Create button.
        ctx["final_assignment"] = getattr(cs, "final_assignment", None)
        return ctx
