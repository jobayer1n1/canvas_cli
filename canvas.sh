#!/usr/bin/env bash

# Source this file to register a canvas() shell function.
# That allows `canvas -scwd` to change the current shell directory.

canvas() {
    local script_dir canvas_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [[ "${1:-}" == "-scwd" || "${1:-}" == "--switch-current-working-directory" ]]; then
        canvas_dir="$(python3 "$script_dir/canvas.py" --switch-current-working-directory)" || return $?
        if [[ -z "$canvas_dir" ]]; then
            return 1
        fi
        mkdir -p "$canvas_dir"
        cd "$canvas_dir" || return $?
        return 0
    fi

    python3 "$script_dir/canvas.py" "$@"
}
