from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import zipfile
from zoneinfo import ZoneInfo

from commands._sync_common import normalize_code, sanitize_name
from utils.localAppData import LocalAppData

HELP = "export command - Creates shareable .canvas archives for course directories"


def _compact_name(value: str) -> str:
    return normalize_code(value).replace(" ", "").replace("-", "").replace("_", "")


def _find_course_directory(sync_base: Path, query: str) -> Path | None:
    direct_path = sync_base / sanitize_name(query)
    if direct_path.is_dir():
        return direct_path

    query_norm = normalize_code(query)
    query_compact = _compact_name(query)
    try:
        course_dirs = [path for path in sync_base.iterdir() if path.is_dir()]
    except OSError:
        return None

    for course_dir in course_dirs:
        dir_norm = normalize_code(course_dir.name)
        dir_compact = _compact_name(course_dir.name)
        first_token = normalize_code(course_dir.name.split(" ")[0])
        if (
            dir_norm == query_norm
            or first_token == query_norm
            or dir_compact == query_compact
            or dir_compact.startswith(query_compact)
        ):
            return course_dir
    return None


def _module_manifest(course_dir: Path) -> dict:
    modules_dir = course_dir / "Modules"
    entries = []
    if not modules_dir.is_dir():
        return {"version": 1, "entries": entries}

    for path in sorted(modules_dir.rglob("*")):
        relative_path = path.relative_to(course_dir).as_posix()
        if path.is_symlink():
            target = path.resolve()
            try:
                target_relative = target.relative_to(course_dir).as_posix()
            except ValueError as exc:
                raise ValueError(f"module link points outside course: {path}") from exc
            entries.append({"path": relative_path, "type": "symlink", "target": target_relative})
        elif path.is_dir():
            entries.append({"path": relative_path, "type": "directory"})
        elif path.is_file():
            raise ValueError(
                f"module entry is a regular file, not a symlink: {path}. Run modulesync first."
            )
    return {"version": 1, "entries": entries}


def _write_course_archive(course_dir: Path, export_dir: Path, username: str) -> Path:
    files_dir = course_dir / "Files"
    if not files_dir.is_dir():
        raise ValueError(f"Files directory does not exist: {files_dir}")

    manifest = _module_manifest(course_dir)
    archive_path = export_dir / f"{course_dir.name}.canvas"
    metadata = {
        "course": course_dir.name,
        "username": username,
        "timestamp": datetime.now(ZoneInfo("Asia/Dhaka")).strftime(
            "%d %B %Y, %I:%M:%S %p (Bangladesh Time)"
        ),
        "modules": manifest,
    }

    export_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("metadata.json", json.dumps(metadata, indent=2) + "\n")
        for path in sorted(files_dir.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Files directory contains a symlink: {path}")
            if path.is_file():
                archive.write(path, Path("Files") / path.relative_to(files_dir))
            elif path.is_dir() and not any(path.iterdir()):
                archive.writestr(str(Path("Files") / path.relative_to(files_dir)) + "/", "")
    return archive_path


def main(argv: list[str]) -> None:
    app_data = LocalAppData()
    sync_settings = app_data.get_sync_directory()
    if not sync_settings or not sync_settings.get("directory"):
        print("Syncing directory has not been set. Try: canvas --syncmanager")
        return

    sync_base = Path(sync_settings["directory"]) / "Canvas"
    export_dir = sync_base / "Exports"
    username = str((app_data.get_user_data() or {}).get("NAME", ""))
    queries = [query.strip() for query in argv if query.strip()]
    if not queries:
        print("Usage: canvas --export COURSE [COURSE ...]")
        return

    for query in queries:
        course_dir = _find_course_directory(sync_base, query)
        if course_dir is None:
            print(f"Course not found: {query}")
            continue
        try:
            archive_path = _write_course_archive(course_dir, export_dir, username)
            print(f"[Exported] {course_dir.name} -> {archive_path}")
        except (OSError, ValueError) as exc:
            print(f"[Error] Could not export {course_dir.name}: {exc}")