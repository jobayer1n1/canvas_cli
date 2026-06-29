#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import sys
import os
from pathlib import Path

# --- Dependency Check ---
def check_dependencies():
    missing_pip = []
    tkinter_missing = False

    # Check for PyPI packages
    try:
        import canvasapi
    except ImportError:
        missing_pip.append("canvasapi")
    
    try:
        import requests
    except ImportError:
        missing_pip.append("requests")

    # Check for Tkinter (System package on Linux)
    try:
        import tkinter
    except ImportError:
        tkinter_missing = True

    if missing_pip or tkinter_missing:
        print("--- Missing Dependencies Detected ---")
        
        if missing_pip:
            print(f"The following Python packages are missing: {', '.join(missing_pip)}")
            if sys.platform == "win32":
                print("Action: Run 'pip install -r requirements.txt'")
            else:
                print("Action: Run 'pip3 install -r requirements.txt'")
            print("-" * 30)

        if tkinter_missing:
            if sys.platform == "linux":
                print("Tkinter is missing (required for folder selection).")
                print("Action: Run 'sudo apt update && sudo apt install python3-tk'")
            else:
                print("Tkinter is missing. Please reinstall Python and ensure 'Tcl/Tk' is checked.")
            print("-" * 30)
        
        sys.exit(1)

# Run the check immediately
check_dependencies()
# ------------------------

from utils.localAppData import LocalAppData


def get_canvas_sync_directory() -> Path | None:
    sync_data = LocalAppData().get_sync_directory()
    if not sync_data or not sync_data.get("directory"):
        return None

    return Path(sync_data["directory"]) / "Canvas"


def handle_no_args() -> None:
    user_data = LocalAppData().get_user_data()
    if not user_data or not user_data.get("NAME"):
        print("You are not logged in. Please run: canvas -li")
        return

    print(f"Hi, {user_data['NAME']}")


def run_command(command: str, argv: list[str]) -> bool:
    try:
        module = importlib.import_module(f"commands.{command}")
    except ModuleNotFoundError as exc:
        if exc.name == f"commands.{command}":
            return False
        raise

    handler = getattr(module, "main", None) or getattr(module, "run", None)
    if handler is None:
        print(f"Command '{command}' has no main() or run() function.")
        return True

    handler(argv)
    return True


def discover_commands() -> list[str]:
    commands_dir = Path(__file__).parent / "commands"
    if not commands_dir.exists():
        return []
    return sorted(
        p.stem
        for p in commands_dir.glob("*.py")
        if p.name not in {"__init__.py"} and not p.name.startswith("_")
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)

    aliases = {
        "login": ["-li", "--login"],  
        "logout": ["-lo", "--logout"],
        "help": ["-h", "--help"],
        "courses": ["-c", "--courses"],
        "showfile": ["-sf", "--showfile"],
        "downloadfile": ["-df", "--downloadfile"],
        "announcements": ["-a", "--announcements"],
        "filesync": ["-fs", "--filesync"],
        "fetch": ["-f", "--fetch"],
        "syncmanager": ["-sm", "--syncmanager"],
        "modulesync": ["-ms", "--modulesync"],
        "reset": ["-r", "--reset"],
        "open": ["-o", "--open"],
    }

    commands = discover_commands()
    for cmd in commands:
        option_strings = [f"--{cmd}"] + aliases.get(cmd, [])
        option_strings = list(dict.fromkeys(option_strings))
        
        parser.add_argument(
            *option_strings,
            action="store_const",
            const=cmd,
            dest="command",
            help=f"run {cmd} command",
        )

    parser.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--print-canvas-dir":
        canvas_dir = get_canvas_sync_directory()
        if canvas_dir is not None:
            canvas_dir.mkdir(parents=True, exist_ok=True)
            print(canvas_dir)
        return

    if len(sys.argv) >= 2 and sys.argv[1] in {"-li", "--login"}:
        from commands.login import main as login_main

        login_main(sys.argv[2:])
        return

    if len(sys.argv) == 1:
        handle_no_args()
        return

    parser = build_parser()
    parsed = parser.parse_args()
    command = parsed.command
    argv = parsed.args

    if not command:
        print("No command provided.")
        print("Try: canvas --help")
        return

    if not LocalAppData().is_valid() and command not in {"login", "help", "open"}:
        print("Please log in first")
        print("Try: canvas --login")
        return
        
    try:
        if not run_command(command, argv):
            print(f"Unknown command: {command}")
            print("Try: canvas --help")
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()
