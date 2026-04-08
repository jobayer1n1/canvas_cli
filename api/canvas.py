from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist, Unauthorized
from canvasapi.course import Course
from canvasapi.canvas import Canvas
from canvasapi.module import Module
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
        except Exception:
            return None

    def get_current_user(self) -> User:
        return self.canvas.get_current_user()

    def get_all_courses(self):
        user = self.canvas.get_current_user()
        courses = user.get_courses(enrollment_state="active")
        return courses

    def get_course_by_id(self, course_id: int | str) -> Course:
        return self.canvas.get_course(course_id)

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

    def get_course_files(self, course: int | str | Course):
        try:
            if isinstance(course, Course):
                target_course = course
            else:
                target_course = self.canvas.get_course(course)
            files = target_course.get_files()
            return files
        except Unauthorized:
            print(f"Error: Not authorized to access files for course {getattr(course, 'name', course)}.")
            return []
        except ResourceDoesNotExist:
            print(f"Error: Course {getattr(course, 'course_code', course)} not found.")
        return []

    def get_course_modules(self, course: int | str | Course):
        try:
            if isinstance(course, Course):
                target_course = course
            else:
                target_course = self.canvas.get_course(course)
            modules = target_course.get_modules()
            return modules
        except Unauthorized:
            print(f"Error: Not authorized to access modules for course {getattr(course, 'name', course)}.")
            return []
        except ResourceDoesNotExist:
            print(f"Error: Course {getattr(course, 'course_code', course)} not found.")
        return []

    def get_module_items(self, module: Module):
        try:
            items = module.get_module_items()
            return items
        except Unauthorized:
            print(f"Error: Not authorized to access items for module {getattr(module, 'name', module)}.")
            return []
        except Exception as e:
            print(f"An unexpected error occurred while reading module items: {e}")
            return []

    def get_course_file_by_content_id(self, course: int | str | Course, content_id: int):
        try:
            if isinstance(course, Course):
                target_course = course
            else:
                target_course = self.canvas.get_course(course)
            file = target_course.get_file(content_id)
            return file
        except Unauthorized:
            print(f"Error: Not authorized to access file content in course {getattr(course, 'name', course)}.")
            return None
        except ResourceDoesNotExist:
            print(f"Error: File content {content_id} not found in course {getattr(course, 'course_code', course)}.")
        return None

    @staticmethod
    def authenticate_token(api_token: str) -> User | None:
        canvas = get_canvas(api_token)
        if canvas is None:
            return None
        api = CanvasAPI(canvas)
        return api.check_credentials()


def get_api_from_token(api_token: str) -> CanvasAPI | None:
    canvas = get_canvas(api_token)
    if canvas is None:
        return None
    return CanvasAPI(canvas)


def get_api() -> CanvasAPI | None:
    canvas = get_canvas()
    if canvas is None:
        return None
    return CanvasAPI(canvas)
