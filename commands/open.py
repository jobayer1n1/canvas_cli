import os
import subprocess
import sys
from pathlib import Path

from utils.localAppData import LocalAppData
from commands._sync_common import resolve_target_codes_from_index, sanitize_name, normalize_code

HELP = "open command - Opens the Canvas sync directory or specific course directories"

def main(argv: list[str]) -> None:
    app_data = LocalAppData()
    sync_dir_dict = app_data.get_sync_directory()
    
    if not sync_dir_dict or "directory" not in sync_dir_dict:
        print("Sync directory is not set. Please set it using canvas --syncmanager.")
        return

    sync_base = Path(sync_dir_dict["directory"]) / "Canvas"
    target_path = sync_base
    
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
            local_index = app_data.get_course_index()
            
            if not local_index or "courses" not in local_index:
                print("No local course metadata found. Please run: canvas --fetch")
                return

            target_codes = resolve_target_codes_from_index(course_query, local_index)
            if not target_codes:
                print(f"Course '{course_query}' not found in enrollment list.")
                return
                
            target_token = sorted(list(target_codes))[0]
            
            course_name = None
            for cd in local_index["courses"]:
                token = normalize_code(cd.get("token", ""))
                base = normalize_code(cd.get("base", ""))
                if token == target_token or base == target_token:
                    course_name = cd.get("name")
                    break
                    
            if not course_name:
                print(f"Course metadata matches were inconclusive for '{course_query}'.")
                return
                
            target_path = sync_base / sanitize_name(course_name)
            
            if want_module:
                target_path = target_path / "Modules"
            elif want_file:
                target_path = target_path / "Files"
                
            if sub_path:
                target_path = target_path / sub_path.lstrip("/\\")
                
    if not target_path.exists():
        print(f"Directory does not exist yet at: {target_path}")
        print("Note: You may need to run `canvas --filesync` or `canvas --modulesync` first.")
        return
        
    print(f"Opening {target_path}...")
    
    if os.name == 'nt':
        os.startfile(target_path)
    elif sys.platform == 'darwin':
        subprocess.run(['open', target_path])
    else:
        subprocess.run(['xdg-open', target_path])
