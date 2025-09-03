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
