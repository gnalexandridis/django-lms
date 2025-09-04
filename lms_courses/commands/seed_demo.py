from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from lms_courses.seed_helpers import seed_catalog_courses, seed_demo_users


class Command(BaseCommand):
    help = "Seed demo data: basic course catalog and demo users (t1/s1)."

    def add_arguments(self, parser):
        parser.add_argument("--no-users", action="store_true", help="Do not create demo users")
        parser.add_argument(
            "--courses",
            nargs="*",
            help=(
                "Optional space-separated course definitions as CODE=Title"
                " (e.g., CS101='Intro to CS')"
            ),
        )

    def handle(self, *args: Any, **options: Any):
        no_users: bool = options.get("no_users", False)
        courses_arg = options.get("courses")

        course_items = None
        if courses_arg:
            parsed = []
            for item in courses_arg:
                if "=" in item:
                    code, title = item.split("=", 1)
                    parsed.append((code, title.strip("'\"")))
            course_items = parsed or None

        courses = seed_catalog_courses(course_items)
        if not no_users:
            users = seed_demo_users()
        else:
            users = []

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(courses)} courses; {len(users)} users."))
