from pathlib import Path
import os
import json
from canvasapi.exceptions import InvalidAccessToken


class LocalAppData:
    def __init__(self):
        self.app_dir = Path(os.environ["LOCALAPPDATA"]) / "canvas-cli"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.user_data = self.app_dir / "user_data.txt"
        self.sync_directory = self.app_dir / "sync_directory.txt"
        self.ignore_list = self.app_dir / "ignore_list.txt"
        self.course_index = self.app_dir / "course_index.txt"



    def save_user_data(self, user_data_to_add: dict[str, str]):
        self.user_data.write_text(json.dumps(user_data_to_add), encoding="utf-8")


    def get_user_data(self):
        if self.user_data.exists():
            return json.loads(self.user_data.read_text(encoding="utf-8"))
        return None
    
    def delete_user_data(self):
        if self.user_data.exists():
            self.user_data.unlink()
            return True
        return False
    
    def is_valid(self):
        from api.canvas import get_api

        api = get_api()
        if api is None or api.check_credentials() is None:
            return False
        return True
        
    def get_sync_directory(self):
        if self.sync_directory.exists():
            return json.loads(self.sync_directory.read_text(encoding="utf-8"))
        return None
    def set_sync_directory(self, sync_directory: dict[str, str]):
        self.sync_directory.write_text(json.dumps(sync_directory), encoding="utf-8")
        return
    def delete_sync_directory(self):
        if self.sync_directory.exists():
            self.sync_directory.unlink()
            return True
        return False

    def set_ignore_list(self, ignore_list_to_add: dict[str,list[str]]):
        self.ignore_list.write_text(json.dumps(ignore_list_to_add), encoding="utf-8")
        return True

    def add_to_ignore_list(self, course_to_add: str):
        ignore_list = self.get_ignore_list()
        if ignore_list is None:
            ignore_list = []
        ignore_list.append(course_to_add.upper())
        self.set_ignore_list({"ignore_list":ignore_list})
        return True
    
    def remove_from_ignore_list(self, course_to_remove: str):
        ignore_list = self.get_ignore_list()
        if ignore_list is None:
            ignore_list = []
        ignore_list.remove(course_to_remove.upper())
        self.set_ignore_list({"ignore_list":ignore_list})
        return True

    def get_ignore_list(self):
        if not self.ignore_list.exists():
            return []

        try:
            json_dump = json.loads(self.ignore_list.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        # Backward-compatible parsing: support both {"ignore_list": [...]} and raw list payloads.
        if isinstance(json_dump, dict):
            ignore_list = json_dump.get("ignore_list", [])
        else:
            ignore_list = json_dump

        if ignore_list is None:
            return []

        if isinstance(ignore_list, (list, tuple, set)):
            return [str(course).upper() for course in ignore_list if course is not None]

        if isinstance(ignore_list, str):
            return [ignore_list.upper()]

        return []
    def delete_ignore_list(self):
        if self.ignore_list.exists():
            self.ignore_list.unlink()
            return True
        return False

    def set_course_index(self, course_index_to_add: dict):
        self.course_index.write_text(json.dumps(course_index_to_add), encoding="utf-8")
        return True

    def get_course_index(self):
        if self.course_index.exists():
            return json.loads(self.course_index.read_text(encoding="utf-8"))
        return None

    def delete_course_index(self):
        if self.course_index.exists():
            self.course_index.unlink()
            return True
        return False

    def reset_all(self):
        self.delete_user_data()
        self.delete_sync_directory()
        self.delete_ignore_list()
        self.delete_course_index()
        return True

    
   
