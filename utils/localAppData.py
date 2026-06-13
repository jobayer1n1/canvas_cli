from pathlib import Path
import os
import json
import sys
from cryptography.fernet import Fernet, InvalidToken
from canvasapi.exceptions import InvalidAccessToken


class LocalAppData:
    def __init__(self):
        # Logic to handle OS differences
        if sys.platform == "win32":
            # Windows: ~/AppData/Local/canvas-cli
            base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        else:
            # Linux/macOS: ~/.local/share/canvas-cli
            # Follows XDG Spec: $XDG_DATA_HOME or ~/.local/share
            base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))

        self.app_dir = base_dir / "canvas-cli"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_data = self.app_dir / "user_data.txt"
        self.token_key = self.app_dir / "token.key"
        self.sync_directory = self.app_dir / "sync_directory.txt"
        self.ignore_list = self.app_dir / "ignore_list.txt"
        self.course_index = self.app_dir / "course_index.txt"

    def save_user_data(self, user_data_to_add: dict[str, str]):
        user_data = dict(user_data_to_add)
        api_token = user_data.get("API_TOKEN")
        if api_token:
            user_data["API_TOKEN"] = self._encrypt_token(api_token)
            user_data["API_TOKEN_ENCRYPTED"] = True
        self.user_data.write_text(json.dumps(user_data), encoding="utf-8")

    def get_user_data(self):
        if self.user_data.exists():
            user_data = json.loads(self.user_data.read_text(encoding="utf-8"))
            if not isinstance(user_data, dict):
                return None

            api_token = user_data.get("API_TOKEN")
            if not api_token:
                return user_data

            if user_data.get("API_TOKEN_ENCRYPTED"):
                decrypted_token = self._decrypt_token(api_token)
                if decrypted_token is None:
                    return None
                user_data["API_TOKEN"] = decrypted_token
                user_data.pop("API_TOKEN_ENCRYPTED", None)
                return user_data

            # Backward compatibility: migrate any legacy plaintext token to encrypted storage.
            migrated_user_data = dict(user_data)
            migrated_user_data["API_TOKEN"] = self._encrypt_token(api_token)
            migrated_user_data["API_TOKEN_ENCRYPTED"] = True
            self.user_data.write_text(json.dumps(migrated_user_data), encoding="utf-8")
            return user_data
        return None
    
    def delete_user_data(self):
        if self.user_data.exists():
            self.user_data.unlink()
            self.delete_token_key()
            return True
        return False
    
    def is_valid(self):
        # Note: Ensure the 'api.canvas' module is in your python path
        try:
            from api.canvas import get_api
            api = get_api()
            if api is None or api.check_credentials() is None:
                return False
            return True
        except ImportError:
            return False
        
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

    def set_ignore_list(self, ignore_list_to_add: dict[str, list[str]]):
        self.ignore_list.write_text(json.dumps(ignore_list_to_add), encoding="utf-8")
        return True

    def add_to_ignore_list(self, course_to_add: str):
        ignore_list = self.get_ignore_list()
        ignore_list.append(course_to_add.upper())
        self.set_ignore_list({"ignore_list": ignore_list})
        return True
    
    def remove_from_ignore_list(self, course_to_remove: str):
        ignore_list = self.get_ignore_list()
        try:
            ignore_list.remove(course_to_remove.upper())
            self.set_ignore_list({"ignore_list": ignore_list})
            return True
        except ValueError:
            return False

    def get_ignore_list(self):
        if not self.ignore_list.exists():
            return []

        try:
            json_dump = json.loads(self.ignore_list.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

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

    def _get_token_key(self) -> bytes:
        if self.token_key.exists():
            return self.token_key.read_bytes()

        key = Fernet.generate_key()
        self.token_key.write_bytes(key)
        return key

    def _encrypt_token(self, token: str) -> str:
        return Fernet(self._get_token_key()).encrypt(token.encode("utf-8")).decode("utf-8")

    def _decrypt_token(self, token: str) -> str | None:
        try:
            decrypted_token = Fernet(self._get_token_key()).decrypt(token.encode("utf-8"))
            return decrypted_token.decode("utf-8")
        except (InvalidToken, OSError, ValueError):
            return None

    def delete_token_key(self):
        if self.token_key.exists():
            self.token_key.unlink()
            return True
        return False

    def reset_all(self):
        self.delete_user_data()
        self.delete_sync_directory()
        self.delete_ignore_list()
        self.delete_course_index()
        self.delete_token_key()
        return True
