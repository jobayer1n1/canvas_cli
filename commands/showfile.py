from __future__ import annotations

from commands._sync_common import prepare_sync

HELP = "show all files available for a course"


def main(argv: list[str]) -> None:
    if not argv:
        print("Usage: canvas -sf <courseName>")
        return

    context = prepare_sync(argv)
    if not context:
        return

    api, _, courses, _, queries = context

    show_headers = len(courses) > 1

    for course in courses:
        course_name = getattr(course, "name", f"Course_{course.id}")
        if show_headers:
            print(f"--- {course_name} ---")

        try:
            files = api.get_course_files(course)
            has_files = False
            for canvas_file in files:
                print(f"[{canvas_file.id}] {canvas_file.display_name}")
                has_files = True

            if not has_files:
                print("No files found.")
        except Exception as exc:
            print(f"Error reading files for {course_name}: {exc}")
