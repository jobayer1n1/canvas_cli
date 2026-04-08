from __future__ import annotations

from datetime import datetime, timezone

from api.canvas import get_api
from commands._sync_common import build_course_index
from utils.localAppData import LocalAppData

HELP = "fetch and refresh local Canvas enrollment metadata"


def main(argv: list[str]) -> None:
    api = get_api()
    if api is None:
        print("Please log in first")
        return

    try:
        user = api.get_current_user()
        courses = list(api.get_all_courses())
    except Exception as e:
        print(f"Failed to fetch metadata: {e}")
        return

    app_data = LocalAppData()
    existing_user_data = app_data.get_user_data() or {}
    user_data = {
        "API_TOKEN": existing_user_data.get("API_TOKEN"),
        "NAME": user.name,
        "USER_ID": user.id,
    }
    app_data.save_user_data(user_data)

    course_index = build_course_index(courses)
    course_index["fetched_at"] = datetime.now(timezone.utc).isoformat()
    app_data.set_course_index(course_index)

    print(
        f"Fetch complete. Updated local metadata for {user.name} with {len(course_index.get('courses', []))} enrolled courses."
    )
