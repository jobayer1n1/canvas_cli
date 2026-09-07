from __future__ import annotations

import json
import ctypes
import getpass
from io import BytesIO
import os
from pathlib import Path
import shutil
import stat
import zipfile

from commands._sync_common import create_symlink, sanitize_name
from utils.canvas_archive import archive_hash, decode_bytes, decode_metadata, decrypt_bytes
from utils.localAppData import LocalAppData

HELP = "import command - Imports .canvas archives and recreates module links"


def _safe_relative_path(value: str, description: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"invalid {description} path: {value}")
    return path


def _is_reparse_point(path: Path) -> bool:
    attributes = getattr(os.stat(path, follow_symlinks=False), "st_file_attributes", 0)
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _make_writable(path: Path) -> None:
    if os.name == "nt":
        ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x80)
    else:
        path.chmod(path.stat().st_mode | stat.S_IWUSR)


def _remove_existing_tree(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if _is_reparse_point(path) or not path.is_dir():
        _make_writable(path)
        path.unlink()
        return
    for child in path.iterdir():
        _remove_existing_tree(child)
    _make_writable(path)
    path.rmdir()


def _extract_files(archive: zipfile.ZipFile, course_dir: Path, course_name: str) -> None:
    for member in archive.infolist():
        member_path = Path(member.filename)
        if not member.filename:
            continue
        if len(member_path.parts) < 2 or member_path.parts[0] != course_name or member_path.parts[1] != "Files":
            raise ValueError(f"unexpected archive entry: {member.filename}")

        relative_path = _safe_relative_path(
            Path(*member_path.parts[2:]).as_posix(), "Files entry"
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


def _parse_args(argv: list[str]) -> tuple[list[Path], str | None]:
    paths, password = [], None
    index = 0
    while index < len(argv):
        value = argv[index]
        if value in {"-p", "--password"}:
            index += 1
            if index >= len(argv):
                raise ValueError(f"{value} requires a value")
            password = argv[index]
        else:
            paths.append(Path(value).expanduser())
        index += 1
    return paths, password


def _import_archive(archive_path: Path, canvas_dir: Path, password: str | None) -> list[Path]:
    with zipfile.ZipFile(archive_path) as archive:
        try:
            metadata, key = decode_metadata(archive.read("metadata.bin"), password)
        except KeyError as exc:
            raise ValueError("archive must contain metadata.bin") from exc
        courses = metadata.get("courses")
        if not isinstance(courses, dict) or not courses:
            raise ValueError("metadata.bin has no valid courses")

        prepared = []
        for course_name, course_metadata in courses.items():
            if not isinstance(course_metadata, dict):
                raise ValueError(f"invalid metadata for course: {course_name}")
            archive_name = course_metadata.get("archive")
            if not isinstance(archive_name, str) or not archive_name:
                raise ValueError(f"course metadata is missing archive: {course_name}")
            plain_archive = archive.read(archive_name)
            if key is not None:
                nonce = decode_bytes(str(course_metadata.get("archive_nonce", "")))
                if len(plain_archive) < 16:
                    raise ValueError(f"encrypted archive is truncated: {course_name}")
                plain_archive = decrypt_bytes(plain_archive[:-16], plain_archive[-16:], nonce, key)
            if archive_hash(plain_archive) != course_metadata.get("archive_hash"):
                raise ValueError(f"archive hash mismatch: {course_name}")
            prepared.append((str(course_name), course_metadata, plain_archive))

        imported = []
        for course_name, course_metadata, plain_archive in prepared:
            safe_course_name = sanitize_name(course_name)
            if not safe_course_name:
                raise ValueError(f"invalid course name: {course_name}")
            course_dir = canvas_dir / safe_course_name
            if course_dir.exists() or course_dir.is_symlink():
                _remove_existing_tree(course_dir)
            course_dir.mkdir(parents=True)
            course_metadata = {
                "course": course_name,
                "sender": metadata.get("sender", {}),
                "timestamp": metadata.get("timestamp"),
                "modules": course_metadata.get("modules", {}),
            }
            (course_dir / "metadata.json").write_text(json.dumps(course_metadata, indent=2) + "\n", encoding="utf-8")
            with zipfile.ZipFile(BytesIO(plain_archive)) as course_archive:
                _extract_files(course_archive, course_dir, course_name)
            _rebuild_modules(course_dir, course_metadata)
            imported.append(course_dir)
    return imported


def main(argv: list[str]) -> None:
    sync_settings = LocalAppData().get_sync_directory()
    if not sync_settings or not sync_settings.get("directory"):
        print("Syncing directory has not been set. Try: canvas --syncmanager")
        return

    try:
        archive_paths, password = _parse_args(argv)
    except ValueError as exc:
        print(f"[Error] {exc}")
        return
    if not archive_paths:
        print("Usage: canvas --import FILE.canvas [FILE.canvas ...] [-p PASSWORD]")
        return

    canvas_dir = Path(sync_settings["directory"]) / "Canvas" / "Imports"
    canvas_dir.mkdir(parents=True, exist_ok=True)
    for archive_path in archive_paths:
        if not archive_path.is_file():
            print(f"[Error] Archive not found: {archive_path}")
            continue
        try:
            with zipfile.ZipFile(archive_path) as archive:
                envelope = archive.read("metadata.bin")
            if json.loads(envelope).get("encrypted") and password is None:
                password = getpass.getpass("Password: ")
            course_dirs = _import_archive(archive_path, canvas_dir, password)
            print(f"[Imported] {archive_path} -> {', '.join(map(str, course_dirs))}")
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            print(f"[Error] Could not import {archive_path}: {exc}")