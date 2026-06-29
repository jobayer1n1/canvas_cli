from canvasapi.exceptions import Unauthorized

from commands._sync_common import (
    build_course_file_path,
    build_folder_paths,
    is_ignored,
    prepare_sync,
    perform_download,
)


HELP = "filesync command - Syncs all course files to your local directory"


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

        try:
            folder_paths = build_folder_paths(api.get_course_folders(course))
            files = api.get_course_files(course)

            for file in files:
                file_path = build_course_file_path(sync_base, course_name, file, folder_paths)

                if file_path.exists() and file_path.stat().st_size == file.size:
                    print(f"  [Skipped] {file.display_name} [FileFound]")
                    stats["skipped"] += 1
                    continue

                is_resume = file_path.exists() and file_path.stat().st_size < file.size
                if is_resume:
                    print(f"  [OnGoing] {file.display_name} [resumeDownloading]", end="", flush=True)
                    status = perform_download(file, file_path, resume=True, verbose=False)
                    if status == "downloaded":
                        print(" [downloaded]")
                        stats["downloaded"] += 1
                        continue

                    print(" [resumeFailed] [freshDownload]", end="", flush=True)
                    try:
                        file_path.unlink()
                    except OSError:
                        pass

                    status = perform_download(file, file_path, resume=False, verbose=False)
                    if status == "downloaded":
                        print(" [downloaded]")
                        stats["downloaded"] += 1
                    else:
                        print(" [error]")
                        stats["error"] += 1
                    continue

                print(f"  [OnGoing] {file.display_name} [downloading]", end="", flush=True)
                status = perform_download(file, file_path, resume=False, verbose=False)
                if status == "downloaded":
                    print(" [downloaded]")
                    stats["downloaded"] += 1
                else:
                    print(" [error]")
                    stats["error"] += 1

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
