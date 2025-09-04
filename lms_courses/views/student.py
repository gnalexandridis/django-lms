from django.shortcuts import get_object_or_404
from django.views.generic import ListView, TemplateView

from lms_users.permissions import RoleRequiredMixin, Roles

from ..models import CourseSemester, LabParticipation, LabReportGrade


class StudentCourseListView(RoleRequiredMixin, ListView):
    template_name = "lms_courses/student/course_list.html"
    context_object_name = "courses"
    allowed_roles = (Roles.STUDENT,)

    def get_queryset(self):
        return (
            CourseSemester.objects.filter(students=self.request.user)
            .select_related("course")
            .order_by("course__code")
        )


# Preserve original callable name for URL imports
student_course_list = StudentCourseListView.as_view()


class StudentCourseDetailView(RoleRequiredMixin, TemplateView):
    template_name = "lms_courses/student/course_detail.html"
    allowed_roles = (Roles.STUDENT,)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        # Ensure the student is enrolled in the requested course semester
        self.cs = get_object_or_404(
            CourseSemester.objects.select_related("course"),
            pk=kwargs.get("pk"),
            students=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request
        cs = self.cs  # type: ignore[attr-defined]

        sessions = list(cs.sessions.all())  # type: ignore

        # Build attendance and grade per session for this student
        att_map = {
            p.session_id: p.present  # type: ignore
            for p in LabParticipation.objects.filter(session__in=sessions, student=request.user)
        }
        grades_map = {
            g.lab_report.session_id: g.grade  # type: ignore
            for g in LabReportGrade.objects.filter(
                lab_report__session__in=sessions, student=request.user
            )
        }

        rows = [
            {
                "session": s,
                "present": bool(att_map.get(s.id, False)),
                "grade": grades_map.get(s.id),
            }
            for s in sessions
        ]

        # Attendance percentage
        attendance_pct = None
        if sessions:
            present_count = sum(1 for r in rows if r["present"])
            attendance_pct = round(100 * present_count / len(sessions))

        # Final assignment result for this student
        fa = getattr(cs, "final_assignment", None)
        fa_res = None
        if fa:
            fa_res = fa.results.filter(student=request.user).first()

        ctx.update(
            {
                "course_semester": cs,
                "rows": rows,
                "attendance_pct": attendance_pct,
                "final_assignment": fa,
                "final_assignment_result": fa_res,
            }
        )
        return ctx
