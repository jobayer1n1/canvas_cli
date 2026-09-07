from __future__ import annotations

from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
import zipfile
from zoneinfo import ZoneInfo

from commands._sync_common import normalize_code, sanitize_name
from utils.canvas_archive import (
    archive_hash,
    derive_key,
    encode_bytes,
    encode_encrypted_metadata,
    encode_plain_metadata,
    encrypt_bytes,
)
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


def _course_zip(course_dir: Path) -> bytes:
    files_dir = course_dir / "Files"
    if not files_dir.is_dir():
        raise ValueError(f"Files directory does not exist: {files_dir}")

    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files_dir.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Files directory contains a symlink: {path}")
            if path.is_file():
                archive.write(path, Path(course_dir.name) / "Files" / path.relative_to(files_dir))
            elif path.is_dir() and not any(path.iterdir()):
                archive.writestr(str(Path(course_dir.name) / "Files" / path.relative_to(files_dir)) + "/", "")
    return output.getvalue()


def _parse_args(argv: list[str]) -> tuple[list[str], str | None, str | None]:
    queries, name, password = [], None, None
    index = 0
    while index < len(argv):
        value = argv[index]
        if value in {"-n", "--name", "-p", "--password"}:
            index += 1
            if index >= len(argv):
                raise ValueError(f"{value} requires a value")
            if value in {"-n", "--name"}:
                name = argv[index]
            else:
                password = argv[index]
        else:
            queries.append(value)
        index += 1
    return queries, name, password


def _write_export(course_dirs: list[Path], export_dir: Path, username: str, name: str, password: str | None) -> Path:
    key = None
    salt = None
    if password is not None:
        salt = os.urandom(16)
        key = derive_key(password, salt)
    blobs, courses = {}, {}
    for course_dir in course_dirs:
        plain_archive = _course_zip(course_dir)
        archive_name = f"{course_dir.name}.zip"
        if key is None:
            archive_data, nonce = plain_archive, None
        else:
            nonce, ciphertext, tag = encrypt_bytes(plain_archive, key)
            archive_data = ciphertext + tag
        blobs[archive_name] = archive_data
        courses[course_dir.name] = {
            "archive": archive_name,
            "archive_hash": archive_hash(plain_archive),
            "archive_nonce": encode_bytes(nonce) if nonce else None,
            "modules": _module_manifest(course_dir),
        }
    metadata = {
        "sender": {"username": username},
        "timestamp": datetime.now(ZoneInfo("Asia/Dhaka")).strftime(
            "%d %B %Y, %I:%M:%S %p (Bangladesh Time)"
        ),
        "courses": courses,
    }
    metadata_bin = encode_plain_metadata(metadata) if key is None else encode_encrypted_metadata(metadata, password, salt, key)
    export_dir.mkdir(parents=True, exist_ok=True)
    archive_path = export_dir / f"{name}.canvas"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("metadata.bin", metadata_bin)
        for archive_name, archive_data in blobs.items():
            archive.writestr(archive_name, archive_data)
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
    try:
        queries, output_name, password = _parse_args(argv)
    except ValueError as exc:
        print(f"[Error] {exc}")
        return
    queries = [query.strip() for query in queries if query.strip()]
    if not queries:
        print("Usage: canvas --export COURSE [COURSE ...] [-n NAME] [-p PASSWORD]")
        return
    if len(queries) > 1 and not output_name:
        print("Error: --name is required when exporting multiple courses.")
        return

    course_dirs = []
    for query in queries:
        course_dir = _find_course_directory(sync_base, query)
        if course_dir is None:
            print(f"Course not found: {query}")
            continue
        course_dirs.append(course_dir)
    if not course_dirs:
        return
    try:
        name = sanitize_name(output_name or course_dirs[0].name)
        archive_path = _write_export(course_dirs, export_dir, username, name, password)
        print(f"[Exported] {', '.join(path.name for path in course_dirs)} -> {archive_path}")
    except (OSError, ValueError) as exc:
        print(f"[Error] Could not export courses: {exc}")