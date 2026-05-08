#!/usr/bin/env python3
from utils.localAppData import LocalAppData
from api.canvas import get_api
from pathlib import Path
import os
import time
import sys

HELP = "syncing config"

def clear_screen():
    """Cross-platform command to clear the terminal screen."""
    # 'cls' for Windows, 'clear' for Linux/macOS
    os.system('cls' if os.name == 'nt' else 'clear')

def choose_folder() -> str | None:
    """Selects a folder via GUI dialog, falling back to manual input if no Display is found."""
    folder = None
    
    # Try GUI first (Works on Windows or Linux with a Desktop environment)
    if os.name == 'nt' or os.environ.get('DISPLAY'):
        try:
            from tkinter import Tk, filedialog
            root = Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            folder = filedialog.askdirectory(title="Select Canvas Sync Directory")
            root.update()
            root.destroy()
        except Exception:
            folder = None

    # Fallback to Terminal Input if GUI fails or isn't available
    if not folder:
        print("\n--- Directory Setup ---")
        while True:
            path_input = input("Enter the absolute path for syncing (or 'q' to cancel): ").strip()
            
            if path_input.lower() == 'q':
                return None
            
            # .expanduser() handles the '~' shortcut in Linux
            target_path = Path(path_input).expanduser().resolve()
            
            if target_path.exists() and target_path.is_dir():
                if os.access(target_path, os.W_OK):
                    return str(target_path)
                else:
                    print(f"Error: Permission denied for {target_path}")
            else:
                print(f"Error: Path '{target_path}' does not exist.")
                create = input("Would you like to create this directory? (y/n): ").lower()
                if create == 'y':
                    try:
                        target_path.mkdir(parents=True, exist_ok=True)
                        return str(target_path)
                    except Exception as e:
                        print(f"Failed to create directory: {e}")
    
    return folder

def main(argv: list[str]) -> None:
    clear_screen()
    api = get_api()
    if api is None:
        print("Please log in first")
        return
    
    available_courses = api.get_all_courses()
    # Store names in Uppercase for consistent matching
    available_courses_names = [course.name.split(" ")[0].upper() for course in available_courses]
    
    # Initial setup if directory isn't set
    if LocalAppData().get_sync_directory() is None:
        print("No sync directory configured.")
        directory = choose_folder()
        if directory:
            LocalAppData().set_sync_directory({"directory": directory})
        else:
            return

    while True:
        sync_data = LocalAppData().get_sync_directory()
        # FIX: Check if sync_data exists AND if the "directory" key has a value
        if not sync_data or sync_data.get("directory") is None:
            print("\n[!] No sync directory configured or data is corrupted.")
            new_dir = choose_folder()
            if new_dir:
                LocalAppData().set_sync_directory({"directory": new_dir})
                continue # Restart the loop with the new data
            else:
                print("Exiting Sync Manager.")
                break
            
        # Now it is safe to create the Path object
        directory = Path(sync_data["directory"]) / "Canvas"
        
        print(f"""
--- Sync Manager ---
Syncing directory: {directory}
> i : modify ignore list
> c : change directory
> q : quit
              """)
        
        try:
            cmd = input("sm> ").lower().strip()

            if cmd == "c":
                new_dir = choose_folder()
                if new_dir:
                    LocalAppData().set_sync_directory({"directory": new_dir})
                continue

            elif cmd == "i":
                clear_screen()
                while True:
                    ignore_list = LocalAppData().get_ignore_list()
                    ignore_list_str = ", ".join(ignore_list) if ignore_list else "None"
                    available_courses_names_str = ", ".join(available_courses_names)
                    
                    print(f"""
Enrolled Courses: {available_courses_names_str}
Ignored Courses: {ignore_list_str}

Enter course name to toggle (e.g., BIO103)
> 'b' to go back
> 'r' to reset ignore list
> 'q' to quit                                        
""")
                    course = input("sm/i> ").strip().upper()
                    
                    if course == "Q":
                        return
                    elif course == "B":
                        clear_screen()
                        break
                    elif course == "R":
                        LocalAppData().delete_ignore_list()
                        print("Ignore list reset.")
                        time.sleep(1)
                        break
                    elif course not in available_courses_names:
                        print(f"Invalid course name: {course}")
                        continue
                    elif course in ignore_list:
                        print(f"Removing {course} from ignore list...")
                        # Assuming your LocalAppData has a remove method; 
                        # if not, you'd handle that logic here.
                        LocalAppData().remove_from_ignore_list(course)
                        time.sleep(1)
                        clear_screen()
                    else:
                        LocalAppData().add_to_ignore_list(course)
                        print(f"Added {course} to ignore list.")
                        time.sleep(1)
                        clear_screen()

            elif cmd == "q":
                break
            else:
                print("Invalid command.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
