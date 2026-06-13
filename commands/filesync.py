from canvasapi.exceptions import Unauthorized
from pathlib import Path

from commands._sync_common import (
    is_ignored,
    prepare_sync,
    sanitize_name,
    sync_file,
)


HELP = "filesync command - Syncs all course files to your local directory"


def _folder_relative_path(folder) -> Path:
    """Return the Canvas folder path below the course root folder."""
    full_name = getattr(folder, "full_name", "") or getattr(folder, "name", "")
    parts = [part.strip() for part in str(full_name).replace("\\", "/").split("/") if part.strip()]

    if parts and parts[0].lower() in {"course files", "files"}:
        parts = parts[1:]

    safe_parts = [sanitize_name(part) for part in parts if sanitize_name(part)]
    return Path(*safe_parts) if safe_parts else Path()


def _build_folder_paths(folders) -> dict[str, Path]:
    return {
        str(folder.id): _folder_relative_path(folder)
        for folder in folders
        if getattr(folder, "id", None) is not None
    }


def main(argv: list[str]) -> None:
    context = prepare_sync(argv)
    if not context:
        return

    api, sync_base, courses, ignore_set, queries = context

    stats = {"downloaded": 0, "skipped": 0, "error": 0}

    for course in courses:
        course_name = getattr(course, "name", f"Course_{course.id}")
        if is_ignored(course, ignore_set):
            print(f"\n--- Skipping: {course_name} (ignored) ---")
            continue

        print(f"\n--- Syncing: {course_name} ---")
        files_dir = sync_base / sanitize_name(course_name) / "Files"

        try:
            folder_paths = _build_folder_paths(api.get_course_folders(course))
            files = api.get_course_files(course)

            for file in files:
                folder_id = str(getattr(file, "folder_id", ""))
                folder_path = folder_paths.get(folder_id, Path())
                safe_file_name = sanitize_name(file.display_name)
                file_path = files_dir / folder_path / safe_file_name
                status = sync_file(file, file_path)
                if status in stats:
                    stats[status] += 1

        except (Unauthorized, Exception) as e:
            if type(e).__name__ in ("Unauthorized", "ResourceDoesNotExist", "Forbidden"):
                print(f"Access Denied: You don't have permission for {course_name} files, or it may have expired.")
                print(f"Please run `canvas --fetch` to update your enrollment list and skip this automatically.")
            else:
                print(f"Error syncing {course_name}: {e}")

    summary = f"Overview: {stats['downloaded']} downloaded | {stats['skipped']} skipped | {stats['error']} errors."
    if queries:
        print(f"\nFinished syncing files for requested courses: {', '.join(queries)}")
    else:
        print("\nFinished syncing all courses.")
    print(summary)
