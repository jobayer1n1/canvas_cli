from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from api.canvas import get_api
from utils.localAppData import LocalAppData


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
        "login": ["-li"],  
        "logout": ["-lo"],
        "help": ["-h"],
        "courses": ["-c"],
        "announcements": ["-a"],
        "filesync": ["-fs"],
        "syncmanager": ["-sm"],
    }

    commands = discover_commands()
    for cmd in commands:
        option_strings = [f"-{cmd}"] + aliases.get(cmd, [])
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
    if len(sys.argv) == 1:
        api = get_api()
        if api is None or api.check_credentials() is None:
            print("""
                Thanks for using canvas-cli
                Try: python app.py -login to log in to your canvas account
                """)
        else:
            name = LocalAppData().get_user_data()["NAME"]
            print(f"""
                Welcome back {name}!!!
                Try: python app.py -help to see all commands
                """)
        return

    parser = build_parser()
    parsed = parser.parse_args()
    command = parsed.command
    argv = parsed.args

    if not command:
        print("No command provided.")
        print("Try: python app.py -help")
        return

    if not LocalAppData().is_valid() and command != "login" and command != "help":
        print("Please log in first")
        print("Try: python app.py -login")
        return
        
    
    try:
        if not run_command(command, argv):
            print(f"Unknown command: {command}")
            print("Try: python app.py -help")
    except KeyboardInterrupt:
        print("\nExiting...")



if __name__ == "__main__":
    main()
