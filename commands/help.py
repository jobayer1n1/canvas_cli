from __future__ import annotations

from pathlib import Path
import importlib

HELP = "See all commmands and their usage"


def main(argv: list[str]) -> None:
    commands_dir = Path(__file__).parent
    names = []
    for p in commands_dir.glob("*.py"):
        if p.name not in {"__init__.py"} and not p.name.startswith("_"):
            names.append(p.stem)

    command_files = sorted(names)


    print("Available commands:")
    if not command_files:
        print("  (none)")
        return
    for name in command_files:
        print(f"  {name}: ",importlib.import_module(f"commands.{name}").HELP)