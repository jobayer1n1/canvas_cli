from utils.localAppData import LocalAppData
HELP = "Reset all configs"
def main(argv: list[str]) -> None:
    user_input = input("Reset won't delete any files from the syncing directory.\nDo you really want to reset all configs? (y/n)")
    if user_input.lower() == "y":
        LocalAppData().reset_all()
        print("All configs have been reset")
    else:
        print("Reset cancelled")
    return