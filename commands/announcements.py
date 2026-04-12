from api.canvas import get_api


HELP = "get all your announcements"

def main(argv: list[str],course_id: int = None) -> None:
    api = get_api()
    if api is None:
        print("Please log in first")
        return
        
    from utils.localAppData import LocalAppData
    app_data = LocalAppData()
    course_index_data = app_data.get_course_index()
    if not course_index_data or "courses" not in course_index_data:
        print("No local course metadata found. Please run: canvas --fetch")
        return
        
    course_ids = [f"course_{cd['id']}" for cd in course_index_data["courses"]]
    if not course_ids:
        print("You have no enrolled courses cached. Try: canvas --fetch")
        return

    announcements = api.canvas.get_announcements(context_codes=course_ids)
    
    course_map = {str(cd["id"]): cd["name"] for cd in course_index_data["courses"]}
    for announcement in announcements:
        c_id_str = announcement.context_code.replace("course_", "")
        c_name = course_map.get(c_id_str, f"Course_{c_id_str}").split(" ")[0]
        print(f"{c_name}: {announcement.title} [{announcement.posted_at}]")
    return
