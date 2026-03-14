from utils.localAppData import LocalAppData
from api.canvas import get_api
from pathlib import Path

HELP="syncing config"

def main(argv: list[str]) -> None:
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
        ignore_list = LocalAppData().get_ignore_list()
        print(f"""
Syncing directory: {directory}
Ignore list: {ignore_list}
> 'i' to modify ignore list
> 'c' to change directory
> 'q' to quit
              """)
        try:
            cmd = input("> ")
            if(cmd=="c"):
                directory=choose_folder()
                if directory==None:
                    print("No directory selected")
                    continue
                LocalAppData().set_sync_directory({"directory":directory})
            elif(cmd=="i"):
                ignore_list=[]
                print(f"""
{available_courses_names}
Enter course name with section which u dont wanna sync
eg: > 'BIO103.1'
>'b' to go back
>'r' to reset ignore list
>'q' to quit                                        
""")
                while True:
                    course = input("> ")
                    if course=="q":
                        return
                    elif course=="r":
                        LocalAppData().delete_ignore_list()
                        break
                    elif course=="b":
                        break
                    elif course not in available_courses_names:
                        print("Invalid course name")
                        continue
                    elif course in ignore_list:
                        print("Course already in ignore list")
                        continue
                    else:
                        ignore_list.append(course.capitalize())
                        jsonified_ignore_list = {
                            "ignore_list":ignore_list
                        }
                        LocalAppData().set_ignore_list(jsonified_ignore_list)
                   

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
