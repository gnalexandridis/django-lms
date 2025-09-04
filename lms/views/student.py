from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import render

from lms_users.decorators import role_required
from lms_users.permissions import Roles


@role_required(Roles.STUDENT)
def student_home(request):
    user = request.user
    role = getattr(user, "role", None)
    if role != Roles.STUDENT:
        return HttpResponse(status=403)

    try:
        days = int(request.GET.get("days", 7))
    except Exception:
        days = 7
    if days not in (3, 7, 14, 30):
        days = 7

    today = date.today()
    soon = today + timedelta(days=days)

    from lms_courses.models import (
        CourseSemester,
        FinalAssignmentResult,
        LabParticipation,
        LabReportGrade,
        LabSession,
    )

    courses = list(
        CourseSemester.objects.filter(students=user)
        .select_related("course")
        .order_by("course__code")
    )

    upcoming_count = LabSession.objects.filter(
        course_semester__in=courses, date__gte=today, date__lte=soon
    ).count()

    grades_qs = LabReportGrade.objects.filter(
        student=user, lab_report__session__course_semester__in=courses
    )
    try:
        overall_avg = round(
            grades_qs.exclude(grade__isnull=True).aggregate(avg=Avg("grade"))["avg"] or 0,
            2,
        )
    except Exception:
        overall_avg = None

    per_course = []
    for cs in courses:
        sessions_total = LabSession.objects.filter(course_semester=cs).count()
        presents = LabParticipation.objects.filter(
            session__course_semester=cs, student=user, present=True
        ).count()
        attendance_pct = None
        if sessions_total > 0:
            attendance_pct = round(100 * presents / sessions_total)

        next_session = (
            LabSession.objects.filter(course_semester=cs, date__gte=today).order_by("date").first()
        )

        course_grades = LabReportGrade.objects.filter(
            lab_report__session__course_semester=cs, student=user
        )
        graded = course_grades.exclude(grade__isnull=True).count()
        avg_grade = course_grades.exclude(grade__isnull=True).aggregate(avg=Avg("grade"))["avg"]

        fa_res = FinalAssignmentResult.objects.filter(
            final_assignment__course_semester=cs, student=user
        ).first()

        per_course.append(
            {
                "cs": cs,
                "attendance_pct": attendance_pct,
                "next_session": next_session,
                "graded_labs": graded,
                "avg_grade": avg_grade,
                "fa_submitted": getattr(fa_res, "submitted", False),
                "fa_grade": getattr(fa_res, "grade", None),
            }
        )

    ctx = {
        "is_student": True,
        "courses": courses,
        "per_course": per_course,
        "total_courses": len(courses),
        "upcoming_labs": upcoming_count,
        "overall_avg_grade": overall_avg,
        "filter_days": days,
        "filter_days_options": [3, 7, 14, 30],
    }
    return render(request, "lms_courses/student/home.html", ctx)
