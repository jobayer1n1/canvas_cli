from __future__ import annotations

import sys

from commands.open import resolve_target_path

HELP = "switch the current terminal working directory to a Canvas course folder"


def main(argv: list[str]) -> None:
    target_path, error = resolve_target_path(argv, for_cwd=True)
    if error:
        print(error, file=sys.stderr)
        raise SystemExit(1)

    print(target_path)
