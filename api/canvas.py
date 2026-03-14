from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist, Unauthorized
from canvasapi.course import Course
from canvasapi.canvas import Canvas
from canvasapi.user import User
from api.canvasObj import get_canvas


class CanvasAPI:
    def __init__(self, canvas: Canvas):
        self.canvas = canvas

    def check_credentials(self) -> User | None:
        try:
            user = self.canvas.get_current_user()
            return user
        except InvalidAccessToken:
            return None

    def get_all_courses(self):
        user = self.canvas.get_current_user()
        courses = user.get_courses(enrollment_state="active")
        return courses

    def get_course_announcements(self, course_id: int):
        announcements = self.canvas.get_announcements(context_codes=[course_id])
        return announcements

    def get_all_courses_announcements(self):
        courses = self.get_all_courses()
        announcements = self.canvas.get_announcements(context_codes=[course.id for course in courses])
        return announcements

    def get_course_files_by_id(self, file_id: int):
        try:
            file = self.canvas.get_file(file_id)
            return file
        except ResourceDoesNotExist:
            print(f"Error: File ID {file_id} not found.")
        except Unauthorized:
            print("Error: Invalid API Key or insufficient permissions for this course.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return []

    def get_course_files(self, course: Course):
        try:
            course = self.canvas.get_course(course)
            files = course.get_files()
            return files
        except Unauthorized:
            print(f"Error: Not authorized to access files for course {getattr(course, 'name', course)}.")
            return []
        except ResourceDoesNotExist:
            print(f"Error: Course ID {course.course_code} not found.")
        return []

def get_api() -> CanvasAPI | None:
    canvas = get_canvas()
    if canvas is None:
        return None
    return CanvasAPI(canvas)
