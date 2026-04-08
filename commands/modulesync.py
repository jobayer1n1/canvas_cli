from canvasapi.exceptions import Unauthorized
from commands._sync_common import (
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

    for course in courses:
        course_name = getattr(course, "name", f"Course_{course.id}")
        safe_course_name = sanitize_name(course_name)
        if is_ignored(course, ignore_set):
            print(f"\n--- Skipping: {course_name} (ignored) ---")
            continue

        print(f"\n--- Syncing Modules for: {course_name} ---")
        try:
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
                            file_path = module_dir / safe_file_name
                            sync_file(file, file_path)
                        except Exception as e:
                            print(f"      [Error] Could not get file details for {item.title}: {e}")

                    elif item.type == 'ExternalUrl':
                        print(f"      [Link] {item.title}: {item.external_url}")

        except Unauthorized:
            print(f"Access Denied for {course_name} modules.")
        except Exception as e:
            print(f"Error syncing {course_name}: {e}")

    if queries:
        print(
            "\nFinished syncing modules for requested courses: "
            + ", ".join(queries)
        )
    else:
        print("\nFinished syncing all modules.")
