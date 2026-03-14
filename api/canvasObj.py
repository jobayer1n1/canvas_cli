from canvasapi import Canvas

API_LINK = "https://northsouth.instructure.com/"
_canvas = None


def get_canvas(token: str | None = None):
    global _canvas
    if token:
        return Canvas(API_LINK, token)
    if _canvas is not None:
        return _canvas

    from utils.localAppData import LocalAppData

    user_data = LocalAppData().get_user_data()
    if not user_data or not user_data.get("API_TOKEN"):
        return None

    _canvas = Canvas(API_LINK, user_data["API_TOKEN"])
    return _canvas
