from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, FormView, ListView, TemplateView

from lms_users.permissions import OwnerRequiredMixin, RoleRequiredMixin, Roles

from ..forms import (
    CourseSemesterForm,
    EnrollmentForm,
    LabParticipationGradeForm,
    LabSessionForm,
)
from ..models import (
    CourseSemester,
    LabParticipation,
    LabReport,
    LabReportGrade,
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
        ctx["students"] = cs.students.all()
        # Provide final_assignment (if implemented as a OneToOne with related_name).
        # Falls back to None so template shows the Create button.
        ctx["final_assignment"] = getattr(cs, "final_assignment", None)
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
        students = list(self.cs.students.all().order_by("username"))
        # Build maps for current participation and grades
        parts = {
            p.student_id: p.present  # type: ignore
            for p in LabParticipation.objects.filter(session=self.session)
        }
        grades = {}
        if self.report:
            grades = {
                g.student_id: g.grade  # type: ignore
                for g in LabReportGrade.objects.filter(lab_report=self.report)
            }
        # Attach convenience attrs for template rendering (no leading underscores)
        for s in students:
            setattr(s, "present_value", bool(parts.get(s.id, False)))
            val = grades.get(s.id)
            setattr(s, "grade_value", "" if val is None else val)

        form = LabParticipationGradeForm(
            session=self.session,
            report=self.report,
            students_qs=self.cs.students.all(),
        )
        context = {
            "course_semester": self.cs,
            "session": self.session,
            "report": self.report,
            "students": students,
            "form": form,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = LabParticipationGradeForm(
            request.POST,
            session=self.session,
            report=self.report,
            students_qs=self.cs.students.all(),
        )
        if form.is_valid():
            form.save()

        return redirect(
            reverse("lms_courses_teacher:course_semester_teacher_detail", kwargs={"pk": self.cs.pk})
        )


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


class EnrollmentCreateView(RoleRequiredMixin, FormView):
    template_name = "lms_courses/teacher/enrollment_form.html"
    form_class = EnrollmentForm
    allowed_roles = (Roles.TEACHER,)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.cs = get_object_or_404(
            CourseSemester.objects.select_related("course"),
            pk=self.kwargs["pk"],
            owner=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["course_semester"] = self.cs
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["E2E_TEST_LOGIN"] = getattr(settings, "E2E_TEST_LOGIN", False)
        q = (self.request.GET.get("q") or "").strip()
        results = []
        if not ctx["E2E_TEST_LOGIN"] and q:
            try:
                results = []
            except Exception:
                results = []
        ctx["query"] = q
        ctx["results"] = results
        return ctx

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "lms_courses_teacher:course_semester_teacher_detail", kwargs={"pk": self.cs.pk}
        )
