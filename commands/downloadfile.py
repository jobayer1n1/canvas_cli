from __future__ import annotations

from pathlib import Path

from canvasapi.exceptions import Forbidden, ResourceDoesNotExist, Unauthorized

from commands._sync_common import prepare_sync, sanitize_name, sync_file

HELP = "download a canvas file by file id"


def _folder_relative_path(folder) -> Path:
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
    if not argv:
        print("Usage: canvas -df <fileId>")
        return

    try:
        file_id = int(argv[0])
    except ValueError:
        print("fileId must be a number")
        return

    context = prepare_sync([])
    if not context:
        return

    api, sync_base, courses, _, _ = context

    try:
        for course in courses:
            course_name = getattr(course, "name", f"Course_{course.id}")
            try:
                canvas_file = None
                for item in api.get_course_files(course):
                    if int(getattr(item, "id", -1)) == file_id:
                        canvas_file = item
                        break

                if canvas_file is None:
                    continue

                folder_paths = _build_folder_paths(api.get_course_folders(course))
                folder_id = str(getattr(canvas_file, "folder_id", ""))
                folder_path = folder_paths.get(folder_id, Path())
                safe_file_name = sanitize_name(canvas_file.display_name)
                local_path = sync_base / sanitize_name(course_name) / "Files" / folder_path / safe_file_name

                print(f"Downloading [{canvas_file.id}] {canvas_file.display_name}")
                status = sync_file(canvas_file, local_path)
                if status == "downloaded":
                    print(f"Saved to {local_path}")
                elif status == "skipped":
                    print(f"Already up to date: {local_path}")
                return
            except (Unauthorized, ResourceDoesNotExist, Forbidden) as exc:
                print(f"Access denied for {course_name}: {exc}")
            except Exception as exc:
                print(f"Error downloading from {course_name}: {exc}")

        print(f"No file found for id {file_id}")
    except (Unauthorized, ResourceDoesNotExist, Forbidden) as exc:
        print(f"Unable to download file {file_id}: {exc}")
    except Exception as exc:
        print(f"Unexpected error while downloading file {file_id}: {exc}")
