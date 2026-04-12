import os
import subprocess
import sys
from pathlib import Path

from utils.localAppData import LocalAppData

HELP = "open command - Opens the Canvas sync directory"

def main(argv: list[str]) -> None:
    app_data = LocalAppData()
    sync_dir_dict = app_data.get_sync_directory()
    
    if not sync_dir_dict or "directory" not in sync_dir_dict:
        print("Sync directory is not set. Please set it using syncmanager.")
        return

    sync_base = Path(sync_dir_dict["directory"]) / "Canvas"
    
    if not sync_base.exists():
        print(f"Canvas directory does not exist at {sync_base}")
        return
        
    print(f"Opening {sync_base}...")
    
    if os.name == 'nt':
        os.startfile(sync_base)
    elif sys.platform == 'darwin':
        subprocess.run(['open', sync_base])
    else:
        subprocess.run(['xdg-open', sync_base])
