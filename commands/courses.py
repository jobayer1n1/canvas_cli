from api.canvas import get_api

HELP = "get all your courses"

def main(argv: list[str]) -> None:
    api = get_api()
    if api is None:
        print("Please log in first")
        return
    courses = api.get_all_courses()
    for course in courses:
        print(course.name)
    return