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


def _find_course_file(api, course, file_id: int):
    for item in api.get_course_files(course):
        try:
            if int(getattr(item, "id", -1)) == file_id:
                return item
        except (TypeError, ValueError):
            continue
    return None


def _build_local_path(sync_base: Path, course_name: str, canvas_file, folder_paths: dict[str, Path]) -> Path:
    folder_id = str(getattr(canvas_file, "folder_id", ""))
    folder_path = folder_paths.get(folder_id, Path())
    safe_file_name = sanitize_name(canvas_file.display_name)
    return sync_base / sanitize_name(course_name) / "Files" / folder_path / safe_file_name


def main(argv: list[str]) -> None:
    if not argv:
        print("Usage: canvas -df <fileId> [fileId...]")
        return

    file_ids: list[int] = []
    for raw_file_id in argv:
        try:
            file_ids.append(int(raw_file_id))
        except ValueError:
            print(f"{raw_file_id} is not a number")

    if not file_ids:
        return

    context = prepare_sync([])
    if not context:
        return

    api, sync_base, courses, _, _ = context
    stats = {"downloaded": 0, "skipped": 0, "error": 0, "not_found": 0}

    for file_id in file_ids:
        found = False
        permission_issue = False

        try:
            for course in courses:
                course_name = getattr(course, "name", f"Course_{course.id}")

                try:
                    canvas_file = _find_course_file(api, course, file_id)
                    if canvas_file is None:
                        continue

                    folder_paths = _build_folder_paths(api.get_course_folders(course))
                    local_path = _build_local_path(sync_base, course_name, canvas_file, folder_paths)

                    print(f"Downloading [{canvas_file.id}] {canvas_file.display_name}")
                    status = sync_file(canvas_file, local_path)
                    if status == "downloaded":
                        print(f"Saved to {local_path}")
                    elif status == "skipped":
                        print(f"Already up to date: {local_path}")
                    if status in stats:
                        stats[status] += 1
                    found = True
                    break
                except (Unauthorized, ResourceDoesNotExist, Forbidden) as exc:
                    permission_issue = True
                    print(f"Access denied for {course_name}: {exc}")
                except Exception as exc:
                    print(f"Error downloading from {course_name}: {exc}")
                    stats["error"] += 1

            if not found and not permission_issue:
                print(f"No file found for id {file_id}")
                stats["not_found"] += 1
        except (Unauthorized, ResourceDoesNotExist, Forbidden) as exc:
            print(f"Unable to download file {file_id}: {exc}")
            stats["error"] += 1
        except Exception as exc:
            print(f"Unexpected error while downloading file {file_id}: {exc}")
            stats["error"] += 1

    print(
        "Overview: "
        f"{stats['downloaded']} downloaded | "
        f"{stats['skipped']} skipped | "
        f"{stats['not_found']} not found | "
        f"{stats['error']} errors."
    )
