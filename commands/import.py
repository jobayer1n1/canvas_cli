from __future__ import annotations

import json
from pathlib import Path
import shutil
import zipfile

from commands._sync_common import create_symlink, sanitize_name
from utils.localAppData import LocalAppData

HELP = "import command - Imports .canvas archives and recreates module links"


def _safe_relative_path(value: str, description: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"invalid {description} path: {value}")
    return path


def _extract_files(archive: zipfile.ZipFile, course_dir: Path) -> None:
    for member in archive.infolist():
        member_path = Path(member.filename)
        if not member.filename or member.filename == "metadata.json":
            continue
        if member_path.parts[0] != "Files":
            raise ValueError(f"unexpected archive entry: {member.filename}")

        relative_path = _safe_relative_path(
            Path(*member_path.parts[1:]).as_posix(), "Files entry"
        )
        destination = course_dir / "Files" / relative_path
        if member.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)


def _rebuild_modules(course_dir: Path, metadata: dict) -> None:
    modules = metadata.get("modules")
    if not isinstance(modules, dict) or not isinstance(modules.get("entries"), list):
        raise ValueError("metadata.json has no valid modules.entries list")

    entries = modules["entries"]
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("module entry must be an object")
        entry_path = _safe_relative_path(str(entry.get("path", "")), "module")
        if not entry_path.parts or entry_path.parts[0] != "Modules":
            raise ValueError(f"module path must be under Modules: {entry_path}")
        destination = course_dir / entry_path
        entry_type = entry.get("type")
        if entry_type == "directory":
            destination.mkdir(parents=True, exist_ok=True)
        elif entry_type == "symlink":
            target_path = _safe_relative_path(str(entry.get("target", "")), "symlink target")
            if not target_path.parts or target_path.parts[0] != "Files":
                raise ValueError(f"symlink target must be under Files: {target_path}")
            target = course_dir / target_path
            if not target.is_file():
                raise ValueError(f"symlink target does not exist: {target_path}")
            if create_symlink(destination, target, verbose=False) == "error":
                raise OSError(f"could not create symlink: {destination}")
        else:
            raise ValueError(f"unknown module entry type: {entry_type}")


def _import_archive(archive_path: Path, canvas_dir: Path) -> Path:
    with zipfile.ZipFile(archive_path) as archive:
        try:
            metadata = json.loads(archive.read("metadata.json"))
        except (KeyError, json.JSONDecodeError) as exc:
            raise ValueError("archive must contain valid metadata.json") from exc

        course_name = str(metadata.get("course", "")).strip()
        if not course_name:
            raise ValueError("metadata.json is missing course")
        safe_course_name = sanitize_name(course_name)
        if not safe_course_name:
            raise ValueError("metadata.json contains an invalid course name")

        course_dir = canvas_dir / safe_course_name
        if course_dir.exists() or course_dir.is_symlink():
            if course_dir.is_dir() and not course_dir.is_symlink():
                shutil.rmtree(course_dir)
            else:
                course_dir.unlink()
        course_dir.mkdir(parents=True)
        archive_metadata = archive.read("metadata.json")
        (course_dir / "metadata.json").write_bytes(archive_metadata)
        _extract_files(archive, course_dir)
        _rebuild_modules(course_dir, metadata)
    return course_dir


def main(argv: list[str]) -> None:
    sync_settings = LocalAppData().get_sync_directory()
    if not sync_settings or not sync_settings.get("directory"):
        print("Syncing directory has not been set. Try: canvas --syncmanager")
        return

    archive_paths = [Path(value).expanduser() for value in argv if value.strip()]
    if not archive_paths:
        print("Usage: canvas --import FILE.canvas [FILE.canvas ...]")
        return

    canvas_dir = Path(sync_settings["directory"]) / "Canvas" / "Imports"
    canvas_dir.mkdir(parents=True, exist_ok=True)
    for archive_path in archive_paths:
        if not archive_path.is_file():
            print(f"[Error] Archive not found: {archive_path}")
            continue
        try:
            course_dir = _import_archive(archive_path, canvas_dir)
            print(f"[Imported] {archive_path} -> {course_dir}")
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            print(f"[Error] Could not import {archive_path}: {exc}")