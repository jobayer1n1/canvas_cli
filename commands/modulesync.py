import os
import re
import requests
from pathlib import Path
from canvasapi.exceptions import Unauthorized
from api.canvas import get_api
from utils.localAppData import LocalAppData

HELP = "Module sync command - Syncs all course modules to your local directory"
CHUNK_SIZE = 1024 * 64 

def sanitize_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '-', name).strip()

def main(argv: list[str]) -> None:
    directory_settings = LocalAppData().get_sync_directory()
    if not directory_settings:
        print("Syncing directory has not been set. Try: syncmanager")
        return

    sync_base = Path(directory_settings["directory"]) / "Canvas"
    sync_base.mkdir(parents=True, exist_ok=True)
    api = get_api()
    if not api:
        print("Please log in first.")
        return

    try:
        courses = api.get_all_courses()
    except Exception as e:
        print(f"Failed to fetch courses: {e}")
        return

    ignore_settings = LocalAppData().get_ignore_list()
    ignore_list = []
    if isinstance(ignore_settings, dict):
        ignore_list = ignore_settings.get("ignore_list", []) or []
    ignore_set = {str(item).strip().lower() for item in ignore_list if str(item).strip()}

    for course in courses:
        course_name = getattr(course, "name", f"Course_{course.id}")
        course_code = getattr(course, "course_code", "")
        short_name = course_name.split(" ")[0] if course_name else ""
        
        safe_course_name = sanitize_name(course_name)

        if ignore_set and (
            course_name.lower() in ignore_set
            or (course_code and course_code.lower() in ignore_set)
            or (short_name and short_name.lower() in ignore_set)
        ):
            print(f"\n--- Skipping: {course_name} (ignored) ---")
            continue
            
        print(f"\n--- Syncing Modules for: {course_name} ---")
        
        try:
            modules = course.get_modules()
            
            for module in modules:
                print(f"\n  Module: {module.name}")
                
                safe_module_name = sanitize_name(module.name)
                module_dir = sync_base / safe_course_name / "Modules" / safe_module_name
                module_dir.mkdir(parents=True, exist_ok=True)

                items = module.get_module_items()
                for item in items:
                    if item.type == 'File':
                        try:
                            file = course.get_file(item.content_id)
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

    print("\nFinished syncing all modules.")


def sync_file(canvas_file, local_path: Path):
    if local_path.exists():
        local_size = local_path.stat().st_size
        
        if local_size == canvas_file.size:
            print(f"  [Skipped] {canvas_file.display_name} (Up to date)")
            return
        elif local_size < canvas_file.size:
            perform_download(canvas_file, local_path, resume=True)
        else:
            perform_download(canvas_file, local_path, resume=False)
    else:
        perform_download(canvas_file, local_path, resume=False)

def perform_download(canvas_file, local_path: Path, resume: bool = False):
    headers = {}
    mode = "wb"
    verb = "Downloading"

    if resume and local_path.exists():
        start_byte = local_path.stat().st_size
        headers['Range'] = f"bytes={start_byte}-"
        mode = "ab"
        verb = "Resuming"

    print(f"  [{verb}] {canvas_file.display_name}... ", end="", flush=True)

    try:
        with requests.get(canvas_file.url, headers=headers, stream=True, timeout=30) as r:
            if resume and r.status_code != 206:
                print(f"    (Resume not supported by server, re-downloading...)")
                mode = "wb"
            
            r.raise_for_status()
            
            with open(local_path, mode) as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
        
        print("[Done]")
                        
    except Exception as e:
        print(f"Failed: {e}")