from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    ListView,
    TemplateView,
)

from lms_users.permissions import OwnerRequiredMixin, RoleRequiredMixin, Roles

from ..forms import (
    CourseSemesterForm,
    LabSessionForm,
)
from ..models import (
    CourseSemester,
    LabReport,
    LabSession,
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
        return ctx


class LabSessionManageView(RoleRequiredMixin, TemplateView):
    template_name = "lms_courses/teacher/lab_session_manage.html"
    allowed_roles = (Roles.TEACHER,)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.cs = get_object_or_404(
            CourseSemester.objects.select_related("course"),
            pk=self.kwargs["pk"],
            owner=request.user,
        )
        self.session = get_object_or_404(
            LabSession, pk=self.kwargs["session_id"], course_semester=self.cs
        )
        # Ensure report exists
        report = getattr(self.session, "report", None)
        if report is None:
            report = LabReport.objects.create(
                session=self.session,
                title=f"Report: {self.session.name}",
                max_grade=10,
                due_date=self.session.date,
            )
        self.report = report
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {
            "course_semester": self.cs,
            "session": self.session,
            "report": self.report,
        }
        return render(request, self.template_name, context)


class LabSessionCreateView(RoleRequiredMixin, CreateView):
    template_name = "lms_courses/teacher/lab_session_form.html"
    form_class = LabSessionForm
    allowed_roles = (Roles.TEACHER,)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.cy = get_object_or_404(
            CourseSemester.objects.select_related("course"),
            pk=self.kwargs["pk"],
            owner=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["course_semester"] = self.cy
        return kwargs

    def get_success_url(self):
        # Redirect to course semester detail view
        return reverse(
            "lms_courses_teacher:course_semester_teacher_detail", kwargs={"pk": self.cy.pk}
        )
