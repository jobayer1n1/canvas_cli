from api.canvas import get_api


HELP = "get all your announcements"

def main(argv: list[str],course_id: int = None) -> None:
    api = get_api()
    if api is None:
        print("Please log in first")
        return
    announcements = api.get_all_courses_announcements()
    for announcement in announcements:
        course_id = announcement.context_code.replace("course_", "")
        course = api.get_course_by_id(course_id)
        print(course.name.split(" ")[0]+": "+announcement.title +" [" +announcement.posted_at+"]")
    return
