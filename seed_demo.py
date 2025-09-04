"""
Standalone seeding helper so you can run: python seed_demo.py

This uses the same helpers as the management command.
"""

from __future__ import annotations

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.settings")
    import django

    django.setup()

    from lms_courses.seed_helpers import seed_catalog_courses, seed_demo_users

    courses = seed_catalog_courses()
    users = seed_demo_users()
    print(f"Seeded {len(courses)} courses; {len(users)} users.")


if __name__ == "__main__":
    # Ensure we can import manage.py sibling modules
    sys.path.insert(0, os.path.dirname(__file__))
    main()
