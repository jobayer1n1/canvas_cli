from api.canvas import get_api

HELP = "get all your courses"

def main(argv: list[str]) -> None:
    from utils.localAppData import LocalAppData
    app_data = LocalAppData()
    course_index_data = app_data.get_course_index()
    if not course_index_data or "courses" not in course_index_data:
        print("No local course metadata found. Please run: canvas --fetch")
        return
        
    for cd in course_index_data["courses"]:
        print(cd["name"])
    return