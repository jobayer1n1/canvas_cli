from canvasapi.exceptions import Unauthorized
from commands._sync_common import (
    build_course_file_path,
    build_folder_paths,
    create_symlink,
    is_ignored,
    prepare_sync,
    sanitize_name,
    sync_file,
)

HELP = "Module sync command - Syncs all course modules to your local directory"


def main(argv: list[str]) -> None:
    context = prepare_sync(argv)
    if not context:
        return

    api, sync_base, courses, ignore_set, queries = context

    stats = {"downloaded": 0, "linked": 0, "skipped": 0, "error": 0}

    for course in courses:
        course_name = getattr(course, "name", f"Course_{course.id}")
        safe_course_name = sanitize_name(course_name)
        if is_ignored(course, ignore_set):
            print(f"\n--- Skipping: {course_name} (ignored) ---")
            continue

        print(f"\n--- Syncing Modules for: {course_name} ---")
        try:
            folder_paths = build_folder_paths(api.get_course_folders(course))
            modules = api.get_course_modules(course)
            for module in modules:
                print(f"\n  Module: {module.name}")
                safe_module_name = sanitize_name(module.name)
                module_dir = sync_base / safe_course_name / "Modules" / safe_module_name
                module_dir.mkdir(parents=True, exist_ok=True)

                items = api.get_module_items(module)
                for item in items:
                    if item.type == 'File':
                        try:
                            file = api.get_course_file_by_content_id(course, item.content_id)
                            if file is None:
                                continue
                            safe_file_name = sanitize_name(file.display_name)
                            canonical_file_path = build_course_file_path(
                                sync_base, course_name, file, folder_paths
                            )
                            module_file_path = module_dir / safe_file_name

                            already_linked = False
                            if module_file_path.exists() or module_file_path.is_symlink():
                                try:
                                    already_linked = (
                                        module_file_path.is_symlink()
                                        and module_file_path.resolve() == canonical_file_path.resolve()
                                    )
                                except OSError:
                                    already_linked = False

                            if already_linked and canonical_file_path.exists():
                                print(f"  [Skipped] {safe_file_name} [FileFound] [AlreadyLinked]")
                                stats["skipped"] += 1
                                continue

                            print(f"  [OnGoing] {safe_file_name}...", end="", flush=True)

                            file_found = canonical_file_path.exists() and canonical_file_path.stat().st_size == file.size
                            if file_found:
                                print(" [FileFound]", end="", flush=True)
                            else:
                                is_resume = canonical_file_path.exists() and canonical_file_path.stat().st_size < file.size
                                print(" [resumeDownload]" if is_resume else " [downloading]", end="", flush=True)
                                download_status = sync_file(file, canonical_file_path, verbose=False)
                                if download_status == "error":
                                    print(" [error]")
                                    stats["error"] += 1
                                    continue
                                stats["downloaded"] += 1
                                print(" [downloaded]", end="", flush=True)

                            print(" [linking]", end="", flush=True)
                            link_status = create_symlink(module_file_path, canonical_file_path, verbose=False)
                            if link_status == "linked":
                                print(" [linked]")
                                stats["linked"] += 1
                            elif link_status == "already_linked":
                                print(" [AlreadyLinked]")
                                stats["skipped"] += 1
                            else:
                                print(" [error]")
                                stats["error"] += 1
                        except Exception as e:
                            print(f"      [Error] Could not get file details for {item.title}: {e}")
                            stats["error"] += 1

                    elif item.type == 'ExternalUrl':
                        print(f"      [Link] {item.title}: {item.external_url}")

        except (Unauthorized, Exception) as e:
            if type(e).__name__ in ("Unauthorized", "ResourceDoesNotExist", "Forbidden"):
                print(f"Access Denied for {course_name} modules. It may have expired.")
                print(f"Please run `canvas --fetch` to update your enrollment list and skip this automatically.")
            else:
                print(f"Error syncing {course_name}: {e}")

    summary = (
        "Overview: "
        f"{stats['downloaded']} downloaded | "
        f"{stats['linked']} linked | "
        f"{stats['skipped']} skipped | "
        f"{stats['error']} errors."
    )
    if queries:
        print(f"\nFinished syncing modules for requested courses: {', '.join(queries)}")
    else:
        print("\nFinished syncing all modules.")
    print(summary)
