from utils.localAppData import LocalAppData
from api.canvas import get_api
from pathlib import Path
import os,time

HELP="syncing config"

def main(argv: list[str]) -> None:
    os.system("cls")
    api = get_api()
    if api is None:
        print("Please log in first")
        return
    
    available_courses = api.get_all_courses()
    available_courses_names = [course.name.split(" ")[0]for course in available_courses]
    
    if LocalAppData().get_sync_directory()==None:
        directory = choose_folder()
        LocalAppData().set_sync_directory({"directory":directory})

        
    while True:
        directory = Path(LocalAppData().get_sync_directory()["directory"]) / "Canvas"
        print(f"""
Syncing directory: {directory}
> 'i' to modify ignore list
> 'c' to change directory
> 'q' to quit
              """)
        try:
            cmd = input("sm> ")
            if(cmd=="c"):
                directory=choose_folder()
                if directory==None:
                    print("No directory selected")
                    continue
                LocalAppData().set_sync_directory({"directory":directory})
            elif(cmd=="i"):
                os.system("cls")
                while True:
                    ignore_list=LocalAppData().get_ignore_list()
                    ignore_list_str = ", ".join(ignore_list)
                    available_courses_names_str = ", ".join(available_courses_names)
                    print(f"""
Enrolled Courses: {available_courses_names_str}
Ignored Courses: {ignore_list_str}

Enter course name with section which u dont wanna sync
eg: > BIO103.1
>'b' to go back
>'r' to reset ignore list
>'q' to quit                                        
""")
                    course = input("sm/i> ").lower()
                    if course=="q":
                        return
                    elif course=="r":
                        LocalAppData().delete_ignore_list()
                        break
                    elif course=="b":
                        os.system("cls")
                        break
                    elif course.upper() not in available_courses_names:
                        print("Invalid course name")
                        continue
                    elif course.upper() in ignore_list:
                        print("Course already in ignore list")
                        continue
                    else:
                        LocalAppData().add_to_ignore_list(course)
                        print("Course added to ignore list")
                        time.sleep(1)
                        os.system("cls")
                        continue
                   

            elif(cmd=="q"):
                return
            else:
                print("Invalid command")
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    
    return





from pathlib import Path
from tkinter import Tk, filedialog

def choose_folder() -> str | None:
    root = Tk()
    root.withdraw() 
    root.attributes("-topmost", True) 
    folder = filedialog.askdirectory(title="Select a directory where Canvas directory will be created to sync")
    root.destroy()
    if not folder:
        return None
    return str(Path(folder).resolve())
