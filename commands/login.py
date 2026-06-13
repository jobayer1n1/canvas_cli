from __future__ import annotations

import argparse
from urllib.parse import urlparse

from api.canvas import CanvasAPI
from utils.remoteCanvasAccessToken import RemoteCanvasAccessToken
from utils.localAppData import LocalAppData

HELP ="log in to your canvas account using API token"


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _parse_login_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="canvas -li", add_help=False)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("-g", "--github", dest="github_source")
    source_group.add_argument("-clp", "--clipnet", dest="clipnet_id")
    parser.add_argument("token_or_source", nargs="?")
    return parser.parse_args(argv)


def main(argv: list[str]) -> None:

    if LocalAppData().is_valid():
        print("Already logged in as "+LocalAppData().get_user_data()["NAME"])
        return

    parsed = _parse_login_args(argv)
    if (parsed.github_source or parsed.clipnet_id) and parsed.token_or_source is not None:
        print("Use either a source flag or a direct token, not both")
        return

    API_TOKEN = None

    if parsed.github_source:
        API_TOKEN = RemoteCanvasAccessToken.fromGithub(parsed.github_source)
        if API_TOKEN is None:
            return
    elif parsed.clipnet_id:
        API_TOKEN = RemoteCanvasAccessToken.clipnet(parsed.clipnet_id)
        if API_TOKEN is None:
            return
    elif parsed.token_or_source is None:
        try:
            API_TOKEN= input("Enter your API token: ")
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    else:
        if _is_url(parsed.token_or_source):
            if "github.com" in parsed.token_or_source or "raw.githubusercontent.com" in parsed.token_or_source:
                API_TOKEN = RemoteCanvasAccessToken.fromGithub(parsed.token_or_source)
            elif "cl1p.net" in parsed.token_or_source:
                API_TOKEN = RemoteCanvasAccessToken.clipnet(parsed.token_or_source.rsplit("/", 1)[-1])
            else:
                API_TOKEN = parsed.token_or_source
        else:
            API_TOKEN = parsed.token_or_source
        if API_TOKEN is None:
            return
        print("[1/2] Using provided access token", flush=True)
    
    if parsed.github_source or parsed.clipnet_id or (_is_url(parsed.token_or_source) if parsed.token_or_source else False):
        print("[4/4] Verifying token with Canvas", flush=True)
    else:
        print("[2/2] Verifying token with Canvas", flush=True)
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
    
