from __future__ import annotations

from typing import Iterable, Sequence

from django.db import transaction

from lms_users.models import User

from .models import Course

DEFAULT_COURSES: Sequence[tuple[str, str]] = (
    ("ΜΥ01", "Υπολογιστικά Μαθηματικά Ι"),
    ("ΥΠ01", "Εισαγωγή στην Πληροφορική και Τηλεματική"),
    ("ΥΠ02", "Προγραμματισμός Ι"),
    ("ΥΠ04", "Λογική Σχεδίαση"),
    ("ΥΠ09", "Διακριτά Μαθηματικά"),
    ("ΜΥ02", "Πιθανότητες"),
    ("ΜΥ03", "Υπολογιστικά Μαθηματικά ΙΙ"),
    ("ΥΠ05", "Προγραμματισμός ΙΙ"),
    ("ΥП08", "Αρχιτεκτονική Υπολογιστών"),
    ("ΥΠ18", "Αντικειμενοστρεφής Προγραμματισμός Ι"),
    ("ΜΥ04", "Στατιστική"),
    ("ΥΠ10", "Αντικειμενοστρεφής Προγραμματισμός ΙΙ"),
    ("ΥΠ11", "Δομές Δεδομένων"),
    ("ΥΠ12", "Λειτουργικά Συστήματα"),
    ("ΥΠ13", "Δίκτυα Υπολογιστών"),
    ("ΥП06", "Σήματα και Συστήματα"),
    ("ΥП16", "Βάσεις Δεδομένων"),
    ("ΥП17", "Ανάλυση Συστημάτων και Τεχνολογία Λογισμικού"),
    ("ΥП19", "Τεχνολογίες Εφαρμογών Ιστού"),
    ("ΥП25", "Αλγόριθμοι και Πολυπλοκότητα"),
    ("ΥП21", "Κατανεμημένα Συστήματα"),
    ("ΥП23", "Τεχνητή Νοημοσύνη"),
    ("ΥП27", "Ασφάλεια Συστημάτων"),
    ("ΥП14", "Τηλεπικοινωνιακά Συστήματα"),
    ("ΥП24", "Μοντελοποίηση και Προσομοίωση Συστημάτων"),
    ("ΥП28", "Πληροφοριακά Συστήματα"),
    ("ΜΥ05", "Μεθοδολογία Επιστημονικής Έρευνας"),
)


@transaction.atomic
def seed_catalog_courses(courses: Iterable[tuple[str, str]] | None = None) -> list[Course]:
    """
    Ensure a minimal course catalog exists.

    Args:
        courses: iterable of (code, title) pairs. If None, uses DEFAULT_COURSES.

    Returns: list of Course objects (created or existing)
    """
    items = list(courses or DEFAULT_COURSES)
    out: list[Course] = []
    for code, title in items:
        obj, _ = Course.objects.get_or_create(code=code, defaults={"title": title})
        # If title changed later in catalog, keep the latest friendly one
        if obj.title != title:
            obj.title = title
            obj.save(update_fields=["title"])
        out.append(obj)
    return out


@transaction.atomic
def seed_demo_users(create_teacher: bool = True, create_student: bool = True) -> list[User]:
    """
    Create basic demo users if they don't exist.

    Users:
      - t1 / x (TEACHER)
      - s1 / x (STUDENT)
    """
    created: list[User] = []
    if create_teacher:
        t1, _ = User.objects.get_or_create(username="t1", defaults={"email": "t1@example.com"})
        if not t1.has_usable_password():
            t1.set_password("x")
        t1.role = "TEACHER"
        t1.save()
        created.append(t1)
    if create_student:
        s1, _ = User.objects.get_or_create(username="s1", defaults={"email": "s1@example.com"})
        if not s1.has_usable_password():
            s1.set_password("x")
        s1.role = "STUDENT"
        s1.save()
        created.append(s1)
    return created
