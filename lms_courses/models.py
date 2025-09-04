from django.conf import settings
from django.db import models


class Course(models.Model):
    # Provided by admin/system; teachers pick from this list
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"


class CourseSemester(models.Model):
    SEMESTER_CHOICES = (("WINTER", "Χειμερινό"), ("SPRING", "Εαρινό"))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="semesters")
    year = models.PositiveIntegerField()
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, default="WINTER")
    enrollment_limit = models.PositiveIntegerField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_semesters"
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="enrolled_course_semesters", blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "year", "semester", "owner"],
                name="uniq_course_semester_per_owner",
            ),
        ]
        ordering = ["-year", "course__code"]

    def get_semester_display(self) -> str:
        return dict(self.SEMESTER_CHOICES).get(self.semester, self.semester)

    def __str__(self) -> str:
        # Include owner and the raw semester code to aid disambiguation in UI and tests
        return f"{self.course} ({self.year} - {self.semester}) - {self.owner}"


class LabSession(models.Model):
    name = models.CharField(max_length=255)
    week = models.PositiveIntegerField()
    date = models.DateField()
    course_semester = models.ForeignKey(
        CourseSemester, on_delete=models.CASCADE, related_name="sessions"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course_semester", "name", "week"], name="uniq_week_per_lab"
            )
        ]
        ordering = ["week"]

    def __str__(self):
        return f"{self.name} — Week {self.week} — {self.course_semester}"

    def clean(self):
        if self.week is not None and self.week <= 0:
            # Keep error type aligned with tests that expect ValueError on create
            raise ValueError("week must be positive")

    def save(self, *args, **kwargs):
        # Validate required fields first to surface TypeError as tests expect
        if self.name is None or self.week is None or self.date is None:
            raise TypeError("Missing required fields: name, week, date")
        # Validate basic invariants before saving
        self.clean()
        saved = super().save(*args, **kwargs)
        # Ensure a LabReport exists for this session (one per session)
        try:
            # Late import-safe access if class defined below
            LabReport  # type: ignore[name-defined]
        except NameError:
            pass
        else:
            from django.utils import timezone

            # Create default lab report if missing
            try:
                _ = self.report  # type: ignore[attr-defined]
            except Exception:
                # Defaults: title derived from session name, max_grade=10, due on session date
                LabReport.objects.create(
                    session=self,
                    title=f"Report: {self.name}",
                    max_grade=10,
                    due_date=getattr(self, "date", timezone.now().date()),
                )
        return saved

    @property
    def present_count(self) -> int:
        try:
            return self.participations.filter(present=True).count()  # type: ignore
        except Exception:
            return 0

    @property
    def graded_count(self) -> int:
        try:
            report = getattr(self, "report", None)
            if not report:
                return 0
            return report.grades.exclude(grade__isnull=True).count()
        except Exception:
            return 0


class FinalAssignment(models.Model):
    title = models.CharField(max_length=255)
    max_grade = models.PositiveIntegerField()
    due_date = models.DateField()
    course_semester = models.OneToOneField(
        CourseSemester, on_delete=models.CASCADE, related_name="final_assignment"
    )

    class Meta:
        ordering = ["due_date"]

    def __str__(self) -> str:
        return f"FinalAssignment({self.title}) — {self.course_semester}"

    def clean(self):
        if self.max_grade is not None and self.max_grade <= 0:
            raise ValueError("max_grade must be positive")

    def save(self, *args, **kwargs):
        if self.title is None or self.max_grade is None or self.due_date is None:
            raise TypeError("Missing required fields: title, max_grade, due_date")
        self.clean()
        return super().save(*args, **kwargs)

    @property
    def submitted_count(self) -> int:
        try:
            return self.results.filter(submitted=True).count()  # type: ignore[attr-defined]
        except Exception:
            return 0

    @property
    def graded_count(self) -> int:
        try:
            return self.results.exclude(grade__isnull=True).count()  # type: ignore[attr-defined]
        except Exception:
            return 0


class LabReport(models.Model):
    title = models.CharField(max_length=255)
    max_grade = models.PositiveIntegerField()
    due_date = models.DateField()
    session = models.OneToOneField(LabSession, on_delete=models.CASCADE, related_name="report")

    class Meta:
        ordering = ["due_date"]

    def __str__(self) -> str:
        return f"LabReport({self.title}) — {self.session}"

    def clean(self):
        if self.max_grade is not None and self.max_grade <= 0:
            raise ValueError("max_grade must be positive")

    def save(self, *args, **kwargs):
        if self.title is None or self.max_grade is None or self.due_date is None:
            raise TypeError("Missing required fields: title, max_grade, due_date")
        self.clean()
        return super().save(*args, **kwargs)


class LabParticipation(models.Model):
    session = models.ForeignKey(LabSession, on_delete=models.CASCADE, related_name="participations")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lab_participations"
    )
    present = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "student"], name="uniq_participation_per_session_student"
            )
        ]
        ordering = ["student__username"]

    def __str__(self) -> str:
        state = "present" if self.present else "absent"
        return f"Participation({self.student} @ {self.session} = {state})"


class LabReportGrade(models.Model):
    lab_report = models.ForeignKey(LabReport, on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lab_report_grades"
    )
    grade = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lab_report", "student"], name="uniq_grade_per_report_student"
            )
        ]
        ordering = ["student__username"]

    def __str__(self) -> str:
        return f"Grade({self.student} @ {self.lab_report} = {self.grade})"


class FinalAssignmentResult(models.Model):
    """Per-student state for the FinalAssignment: submission and grade."""

    final_assignment = models.ForeignKey(
        FinalAssignment, on_delete=models.CASCADE, related_name="results"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="final_assignment_results"
    )
    submitted = models.BooleanField(default=False)
    grade = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["final_assignment", "student"],
                name="uniq_final_assignment_result_per_student",
            )
        ]
        ordering = ["student__username"]

    def __str__(self) -> str:
        sub = "submitted" if self.submitted else "not-submitted"
        return (
            f"FinalAssignmentResult({self.student} @ {self.final_assignment} = "
            f"{sub}, {self.grade})"
        )
