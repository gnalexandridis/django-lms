from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Avg, Count, Q, QuerySet

from lms_courses.models import (
    CourseSemester,
    FinalAssignment,
    LabReportGrade,
    LabSession,
)


def compute_dashboard_stats(user, days: int, selected_course_id: int) -> dict:
    """Return computed dashboard stats for a user, given filters.

    Output keys align with the context used by the dashboard template.
    """
    today = date.today()
    soon = today + timedelta(days=days)

    all_courses_qs: QuerySet[CourseSemester] = CourseSemester.objects.filter(
        owner=user
    ).select_related("course")
    if selected_course_id and all_courses_qs.filter(id=selected_course_id).exists():
        cs_qs = all_courses_qs.filter(id=selected_course_id)
    else:
        cs_qs = all_courses_qs

    active_courses = cs_qs.count()
    unique_students = cs_qs.values("students").exclude(students__isnull=True).distinct().count()
    upcoming_labs = LabSession.objects.filter(
        course_semester__in=cs_qs, date__gte=today, date__lte=soon
    ).count()

    lab_grades_done = LabReportGrade.objects.filter(
        lab_report__session__course_semester__in=cs_qs, grade__isnull=False
    ).count()
    lab_grades_null = LabReportGrade.objects.filter(
        lab_report__session__course_semester__in=cs_qs, grade__isnull=True
    ).count()

    fa_qs = FinalAssignment.objects.filter(course_semester__in=cs_qs)
    fa_submitted = fa_qs.aggregate(c=Count("results", filter=Q(results__submitted=True)))["c"] or 0
    fa_graded = (
        fa_qs.aggregate(c=Count("results", filter=Q(results__grade__isnull=False)))["c"] or 0
    )
    fa_avg = fa_qs.aggregate(avg=Avg("results__grade"))["avg"]

    overdue_ungraded = (
        LabSession.objects.filter(
            course_semester__in=cs_qs,
            date__lt=today - timedelta(days=7),
            report__grades__grade__isnull=True,
        )
        .distinct()
        .count()
    )
    no_attendance_sessions = (
        LabSession.objects.filter(course_semester__in=cs_qs)
        .exclude(participations__isnull=False)
        .count()
    )

    per_course = (
        cs_qs.annotate(
            students_count=Count("students", distinct=True),
            upcoming_sessions=Count(
                "sessions",
                filter=Q(sessions__date__gte=today, sessions__date__lte=soon),
                distinct=True,
            ),
            lab_done=Count(
                "sessions__report__grades",
                filter=Q(sessions__report__grades__grade__isnull=False),
            ),
            lab_null=Count(
                "sessions__report__grades",
                filter=Q(sessions__report__grades__grade__isnull=True),
            ),
            fa_sub=Count(
                "final_assignment__results",
                filter=Q(final_assignment__results__submitted=True),
            ),
            fa_grd=Count(
                "final_assignment__results",
                filter=Q(final_assignment__results__grade__isnull=False),
            ),
        )
        .select_related("course")
        .order_by("course__code")
    )

    trend = []
    for weeks_ago in range(4, 0, -1):
        start = today - timedelta(days=7 * weeks_ago)
        end = start + timedelta(days=6)
        count = LabReportGrade.objects.filter(
            lab_report__session__course_semester__in=cs_qs,
            lab_report__session__date__gte=start,
            lab_report__session__date__lte=end,
            grade__isnull=False,
        ).count()
        trend.append(count)

    return {
        "all_courses_qs": all_courses_qs,
        "cs_qs": cs_qs,
        "active_courses": active_courses,
        "unique_students": unique_students,
        "upcoming_labs": upcoming_labs,
        "lab_grades_done": lab_grades_done,
        "lab_grades_null": lab_grades_null,
        "fa_submitted": fa_submitted,
        "fa_graded": fa_graded,
        "fa_avg": fa_avg,
        "overdue_ungraded": overdue_ungraded,
        "no_attendance_sessions": no_attendance_sessions,
        "per_course": per_course,
        "attendance_trend": trend,
    }
