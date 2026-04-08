from canvasapi.exceptions import Unauthorized
from commands._sync_common import (
    is_ignored,
    prepare_sync,
    sanitize_name,
    sync_file,
)


HELP = "filesync command - Syncs all course files to your local directory"

def main(argv: list[str]) -> None:
    context = prepare_sync(argv)
    if not context:
        return

    api, sync_base, courses, ignore_set, queries = context

    for course in courses:
        course_name = getattr(course, "name", f"Course_{course.id}")
        if is_ignored(course, ignore_set):
            print(f"\n--- Skipping: {course_name} (ignored) ---")
            continue

        print(f"\n--- Syncing: {course_name} ---")
        files_dir = sync_base / sanitize_name(course_name) / "Files"

        try:
            files_dir.mkdir(parents=True, exist_ok=True)
            files = api.get_course_files(course)

            for file in files:
                safe_file_name = sanitize_name(file.display_name)
                file_path = files_dir / safe_file_name
                sync_file(file, file_path)

        except Unauthorized:
            print(f"Access Denied: You don't have permission for {course_name} files.")
        except Exception as e:
            print(f"Error syncing {course_name}: {e}")

    if queries:
        print(
            "\nFinished syncing files for requested courses: "
            + ", ".join(queries)
        )
    else:
        print("\nFinished syncing all courses.")
