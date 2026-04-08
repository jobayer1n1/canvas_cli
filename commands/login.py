from api.canvas import CanvasAPI
from utils.localAppData import LocalAppData

HELP ="log in to your canvas account using API token"

def main(argv: list[str]) -> None:

    if LocalAppData().is_valid():
        print("Already logged in as "+LocalAppData().get_user_data()["NAME"])
        return
    API_TOKEN = None
    if len(argv)==0:
        try:
            API_TOKEN= input("Enter your API token: ")
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    else:
        API_TOKEN = argv[0]
    
    user = CanvasAPI.authenticate_token(API_TOKEN)
    if user is None:
        print("Invalid API TOKEN")
        return

    user_data = {
        "API_TOKEN":API_TOKEN,
        "NAME":user.name,
        "USER_ID":user.id
    }
    LocalAppData().save_user_data(user_data)
    print("Logged in successfully")
    
