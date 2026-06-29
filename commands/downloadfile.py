from __future__ import annotations

from pathlib import Path

from canvasapi.exceptions import Forbidden, ResourceDoesNotExist, Unauthorized

from commands._sync_common import (
    build_course_file_path,
    build_folder_paths,
    perform_download,
    prepare_sync,
)

HELP = "download a canvas file by file id"


def _find_course_file(api, course, file_id: int):
    for item in api.get_course_files(course):
        try:
            if int(getattr(item, "id", -1)) == file_id:
                return item
        except (TypeError, ValueError):
            continue
    return None


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

                    folder_paths = build_folder_paths(api.get_course_folders(course))
                    local_path = build_course_file_path(sync_base, course_name, canvas_file, folder_paths)

                    if local_path.exists() and local_path.stat().st_size == canvas_file.size:
                        print(f"  [Skipped] {canvas_file.display_name} [FileFound]")
                        stats["skipped"] += 1
                        found = True
                        break

                    is_resume = local_path.exists() and local_path.stat().st_size < canvas_file.size
                    if is_resume:
                        print(f"  [OnGoing] {canvas_file.display_name} [resumeDownloading]", end="", flush=True)
                        status = perform_download(canvas_file, local_path, resume=True, verbose=False)
                        if status == "downloaded":
                            print(" [downloaded]")
                            stats["downloaded"] += 1
                            found = True
                            break

                        print(" [resumeFailed] [freshDownload]", end="", flush=True)
                        try:
                            local_path.unlink()
                        except OSError:
                            pass

                        status = perform_download(canvas_file, local_path, resume=False, verbose=False)
                        if status == "downloaded":
                            print(" [downloaded]")
                            stats["downloaded"] += 1
                        else:
                            print(" [error]")
                            stats["error"] += 1
                        found = True
                        break

                    print(f"  [OnGoing] {canvas_file.display_name} [downloading]", end="", flush=True)
                    status = perform_download(canvas_file, local_path, resume=False, verbose=False)
                    if status == "downloaded":
                        print(" [downloaded]")
                        stats["downloaded"] += 1
                    else:
                        print(" [error]")
                        stats["error"] += 1
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
