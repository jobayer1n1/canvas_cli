from __future__ import annotations

import html
import re
from urllib.parse import urlparse

import requests


class RemoteCanvasAccessToken:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    @classmethod
    def fromGithub(cls, source: str) -> str | None:
        return cls()._from_github(source)

    @classmethod
    def clipnet(cls, clip_id: str) -> str | None:
        return cls()._from_clipnet(clip_id)

    def _from_github(self, source: str) -> str | None:
        print(f"[1/4] Fetching GitHub source: {source}", flush=True)

        for candidate_url in self._github_candidates(source):
            print(f"      Trying: {candidate_url}", flush=True)
            try:
                response = requests.get(candidate_url, timeout=self.timeout)
                response.raise_for_status()
            except requests.RequestException:
                continue

            print("[2/4] Reading first line from GitHub response", flush=True)
            token = self._first_line(response.text)
            if not token:
                print("GitHub file did not contain a usable first line")
                return None

            print("[3/4] Token retrieved from GitHub source", flush=True)
            return token

        print("Failed to fetch token from GitHub")
        return None

    def _from_clipnet(self, clip_id: str) -> str | None:
        clip_id = clip_id.strip().strip("/")
        if not clip_id:
            print("Clipnet id is empty")
            return None

        url = f"https://cl1p.net/{clip_id}"
        print(f"[1/4] Fetching cl1p source: {url}", flush=True)
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Failed to fetch cl1p source: {exc}")
            return None

        print("[2/4] Reading cl1p content field", flush=True)
        token = self._extract_cl1p_content(response.text)
        if not token:
            print("cl1p page did not contain a usable token")
            return None

        print("[3/4] Token retrieved from cl1p source", flush=True)
        return token

    def _github_candidates(self, source: str) -> list[str]:
        normalized = source.strip()

        if normalized.startswith("https://raw.githubusercontent.com/"):
            return [normalized]

        parsed = urlparse(normalized)
        if parsed.scheme in {"http", "https"} and "github.com" in parsed.netloc:
            path_parts = [part for part in parsed.path.split("/") if part]
        else:
            path_parts = [part for part in normalized.split("/") if part]

        if len(path_parts) < 3:
            return []

        owner, repo = path_parts[0], path_parts[1]
        remainder = path_parts[2:]

        if remainder and remainder[0] == "blob" and len(remainder) >= 3:
            branch = remainder[1]
            file_path = "/".join(remainder[2:])
            return [f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"]

        if remainder and remainder[0] == "raw" and len(remainder) >= 3:
            branch = remainder[1]
            file_path = "/".join(remainder[2:])
            return [f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"]

        file_path = "/".join(remainder)
        return [
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}",
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/{file_path}",
        ]

    @staticmethod
    def _first_line(text: str) -> str:
        lines = text.splitlines()
        return lines[0].strip() if lines else ""

    @staticmethod
    def _extract_cl1p_content(text: str) -> str:
        match = re.search(
            r'<textarea\b[^>]*name=["\']content["\'][^>]*>(.*?)</textarea>',
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return ""

        return html.unescape(match.group(1)).strip()
