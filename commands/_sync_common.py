from __future__ import annotations

import re
from pathlib import Path

import requests

from api.canvas import get_api
from utils.localAppData import LocalAppData

CHUNK_SIZE = 1024 * 64


def sanitize_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "-", name).strip()


def normalize_code(value: str) -> str:
    return value.strip().lower()


def split_code_section(course_code: str) -> tuple[str, str | None]:
    token = course_code.strip()
    if "." not in token:
        return token, None
    base, section = token.split(".", 1)
    return base, section


def get_course_token(course) -> str:
    course_name = getattr(course, "name", "")
    return (course_name.split(" ")[0] if course_name else "").strip()


def build_course_index(courses) -> dict:
    entries = []
    for course in courses:
        token = get_course_token(course)
        base, section = split_code_section(token)
        entries.append(
            {
                "id": str(getattr(course, "id", "")),
                "name": getattr(course, "name", ""),
                "token": token,
                "base": base,
                "section": section,
            }
        )
    return {"courses": entries}


def get_ignore_set(app_data: LocalAppData) -> set[str]:
    ignore_settings = app_data.get_ignore_list()
    ignore_list = []
    if isinstance(ignore_settings, dict):
        ignore_list = ignore_settings.get("ignore_list", []) or []
    return {normalize_code(str(item)) for item in ignore_list if str(item).strip()}


def is_ignored(course, ignore_set: set[str]) -> bool:
    if not ignore_set:
        return False
    course_name = getattr(course, "name", "")
    course_code = getattr(course, "course_code", "")
    short_name = get_course_token(course)
    return (
        normalize_code(course_name) in ignore_set
        or (course_code and normalize_code(course_code) in ignore_set)
        or (short_name and normalize_code(short_name) in ignore_set)
    )


def resolve_target_codes_from_index(query: str, index_data: dict | None) -> set[str]:
    if not index_data or "courses" not in index_data:
        return set()

    normalized_query = normalize_code(query)
    query_base, _ = split_code_section(normalized_query)
    targets = set()
    for row in index_data.get("courses", []):
        token = normalize_code(row.get("token", ""))
        base = normalize_code(row.get("base", ""))
        if token == normalized_query or base == query_base:
            targets.add(token)
    return targets


def prepare_sync(argv: list[str]):
    app_data = LocalAppData()
    directory_settings = app_data.get_sync_directory()
    if not directory_settings:
        print("Syncing directory has not been set. Try: syncmanager")
        return None

    sync_base = Path(directory_settings["directory"]) / "Canvas"
    sync_base.mkdir(parents=True, exist_ok=True)

    api = get_api()
    if not api:
        print("Please log in first.")
        return None

    try:
        courses = list(api.get_all_courses())
    except Exception as e:
        print(f"Failed to fetch courses: {e}")
        return None

    ignore_set = get_ignore_set(app_data)

    queries = [item.strip() for item in argv if item.strip()]
    if not queries:
        return api, sync_base, courses, ignore_set, None

    local_index = app_data.get_course_index()
    requested_target_codes: set[str] = set()
    missing_queries: list[str] = []
    for query in queries:
        target_codes = resolve_target_codes_from_index(query, local_index)
        if not target_codes:
            missing_queries.append(normalize_code(query))
            continue
        requested_target_codes.update(target_codes)

    if missing_queries:
        for missing in sorted(set(missing_queries)):
            print(
                f"{missing} is not in your enrollment list. use -fetch to update the enrollment course list"
            )
        return None

    target_courses = []
    for course in courses:
        token = normalize_code(get_course_token(course))
        if token in requested_target_codes:
            target_courses.append(course)

    if not target_courses:
        print("No requested courses are currently active. use -fetch to update the enrollment course list")
        return None

    pretty_codes = ", ".join(sorted(requested_target_codes))
    print(f"Resolved requested courses from local storage: {pretty_codes}")
    return api, sync_base, target_courses, ignore_set, queries


def sync_file(canvas_file, local_path: Path):
    if local_path.exists():
        local_size = local_path.stat().st_size

        if local_size == canvas_file.size:
            print(f"  [Skipped] {canvas_file.display_name} (Up to date)")
            return
        if local_size < canvas_file.size:
            perform_download(canvas_file, local_path, resume=True)
            return
    perform_download(canvas_file, local_path, resume=False)


def perform_download(canvas_file, local_path: Path, resume: bool = False):
    headers = {}
    mode = "wb"
    verb = "Downloading"

    if resume and local_path.exists():
        start_byte = local_path.stat().st_size
        headers["Range"] = f"bytes={start_byte}-"
        mode = "ab"
        verb = "Resuming"

    print(f"  [{verb}] {canvas_file.display_name}... ", end="", flush=True)

    try:
        with requests.get(canvas_file.url, headers=headers, stream=True, timeout=30) as r:
            if resume and r.status_code != 206:
                print("    (Resume not supported by server, re-downloading...)")
                mode = "wb"

            r.raise_for_status()

            with open(local_path, mode) as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

        print("[Done]")

    except Exception as e:
        print(f"Failed: {e}")
