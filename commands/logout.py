import os
from pathlib import Path
from utils.localAppData import LocalAppData

HELP = "log out of your canvas account"

def main(argv: list[str]) -> None:
    flag = LocalAppData().delete_user_data()
    if flag:
        print("Logged out successfully")
    else:
        print("No user data found\nLog in first")
    return