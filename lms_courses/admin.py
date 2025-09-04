from django.contrib import admin

from .models import (
    Course,
    CourseSemester,
    FinalAssignment,
    FinalAssignmentResult,
    LabParticipation,
    LabReport,
    LabReportGrade,
    LabSession,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title")
    ordering = ("code",)


class LabParticipationInline(admin.TabularInline):
    model = LabParticipation
    extra = 0
    autocomplete_fields = ("student",)


class LabReportInline(admin.StackedInline):
    model = LabReport
    extra = 0
    max_num = 1
    can_delete = True


@admin.register(LabSession)
class LabSessionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "week",
        "date",
        "course_semester",
        "present_count",
        "graded_count",
    )
    list_filter = (
        "course_semester__course",
        "course_semester__year",
        "course_semester__semester",
    )
    search_fields = (
        "name",
        "course_semester__course__code",
        "course_semester__course__title",
    )
    inlines = [LabReportInline, LabParticipationInline]
    ordering = ("course_semester", "week")
    autocomplete_fields = ("course_semester",)
    readonly_fields = ("present_count", "graded_count")


class LabSessionInline(admin.TabularInline):
    model = LabSession
    extra = 0
    show_change_link = True
    ordering = ("week",)


class FinalAssignmentInline(admin.StackedInline):
    model = FinalAssignment
    extra = 0
    max_num = 1
    can_delete = True


@admin.register(CourseSemester)
class CourseSemesterAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "year",
        "semester",
        "owner",
        "enrollment_limit",
        "students_count",
    )
    list_filter = ("year", "semester", "owner")
    search_fields = ("course__code", "course__title", "owner__username")
    ordering = ("-year", "course__code")
    inlines = [FinalAssignmentInline, LabSessionInline]
    autocomplete_fields = ("course", "owner")
    filter_horizontal = ("students",)

    @admin.display(description="Students")
    def students_count(self, obj: CourseSemester) -> int:  # type: ignore[name-defined]
        return obj.students.count()


class FinalAssignmentResultInline(admin.TabularInline):
    model = FinalAssignmentResult
    extra = 0
    autocomplete_fields = ("student",)


@admin.register(FinalAssignment)
class FinalAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "max_grade",
        "due_date",
        "course_semester",
        "submitted_count",
        "graded_count",
    )
    list_filter = ("due_date",)
    search_fields = (
        "title",
        "course_semester__course__code",
        "course_semester__course__title",
    )
    inlines = [FinalAssignmentResultInline]
    autocomplete_fields = ("course_semester",)
    readonly_fields = ("submitted_count", "graded_count")


class LabReportGradeInline(admin.TabularInline):
    model = LabReportGrade
    extra = 0
    autocomplete_fields = ("student",)


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ("title", "max_grade", "due_date", "session")
    list_filter = ("due_date",)
    search_fields = (
        "title",
        "session__name",
        "session__course_semester__course__code",
    )
    inlines = [LabReportGradeInline]
    autocomplete_fields = ("session",)


@admin.register(LabParticipation)
class LabParticipationAdmin(admin.ModelAdmin):
    list_display = ("session", "student", "present")
    list_filter = ("present", "session__course_semester__course")
    search_fields = (
        "session__name",
        "student__username",
        "session__course_semester__course__code",
    )
    autocomplete_fields = ("session", "student")


@admin.register(LabReportGrade)
class LabReportGradeAdmin(admin.ModelAdmin):
    list_display = ("lab_report", "student", "grade")
    list_filter = ("grade",)
    search_fields = (
        "lab_report__title",
        "student__username",
        "lab_report__session__course_semester__course__code",
    )
    autocomplete_fields = ("lab_report", "student")


@admin.register(FinalAssignmentResult)
class FinalAssignmentResultAdmin(admin.ModelAdmin):
    list_display = ("final_assignment", "student", "submitted", "grade")
    list_filter = ("submitted",)
    search_fields = (
        "final_assignment__title",
        "student__username",
        "final_assignment__course_semester__course__code",
    )
    autocomplete_fields = ("final_assignment", "student")
