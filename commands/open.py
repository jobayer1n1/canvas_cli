import os
import subprocess
import sys
from pathlib import Path

from utils.localAppData import LocalAppData
from commands._sync_common import sanitize_name, normalize_code

HELP = "open command - Opens the Canvas sync directory or specific course directories"


def _compact_name(value: str) -> str:
    return normalize_code(value).replace(" ", "").replace("-", "").replace("_", "")


def _find_course_directory(sync_base: Path, course_query: str) -> Path | None:
    safe_query = sanitize_name(course_query)
    direct_path = sync_base / safe_query
    if direct_path.is_dir():
        return direct_path

    query_norm = normalize_code(course_query)
    query_compact = _compact_name(course_query)

    try:
        course_dirs = [path for path in sync_base.iterdir() if path.is_dir()]
    except OSError:
        return None

    for course_dir in course_dirs:
        dir_name = course_dir.name
        dir_norm = normalize_code(dir_name)
        dir_compact = _compact_name(dir_name)
        first_token = normalize_code(dir_name.split(" ")[0]) if dir_name else ""

        if (
            dir_norm == query_norm
            or first_token == query_norm
            or dir_compact == query_compact
            or dir_compact.startswith(query_compact)
        ):
            return course_dir

    return None


def main(argv: list[str]) -> None:
    app_data = LocalAppData()
    sync_dir_dict = app_data.get_sync_directory()
    
    if not sync_dir_dict or "directory" not in sync_dir_dict:
        print("Sync directory is not set. Please set it using canvas --syncmanager.")
        return

    sync_base = Path(sync_dir_dict["directory"]) / "Canvas"
    target_path = sync_base
    course_query = "Canvas"
    
    if argv:
        args = [arg.strip() for arg in argv if arg.strip()]
        want_module = False
        want_file = False
        sub_path = ""
        course_query_parts = []
        
        for i, a in enumerate(args):
            if a in ("-m", "--modules"):
                want_module = True
                if i + 1 < len(args):
                    sub_path = " ".join(args[i+1:])
                break
            elif a in ("-f", "--files"):
                want_file = True
                if i + 1 < len(args):
                    sub_path = " ".join(args[i+1:])
                break
            else:
                course_query_parts.append(a)
                
        if course_query_parts:
            course_query = "".join(course_query_parts)
            course_path = _find_course_directory(sync_base, course_query)
            if course_path is None:
                print(f"No data regarding {course_query}")
                return
                
            target_path = course_path
            
            if want_module:
                target_path = target_path / "Modules"
            elif want_file:
                target_path = target_path / "Files"
                
            if sub_path:
                target_path = target_path / sub_path.lstrip("/\\")
                
    if not target_path.exists():
        print(f"No data regarding {course_query}")
        return
        
    print(f"Opening {target_path}...")
    
    if os.name == 'nt':
        os.startfile(target_path)
    elif sys.platform == 'darwin':
        subprocess.run(['open', target_path])
    else:
        subprocess.run(['xdg-open', target_path])
