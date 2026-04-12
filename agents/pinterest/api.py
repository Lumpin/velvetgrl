"""Pinterest API v5 client — OAuth flow, pin creation, board management."""

import base64
import json
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import httpx

from agents.config import CONFIG_DIR, load_settings

API_BASE = "https://api.pinterest.com/v5"
AUTH_URL = "https://www.pinterest.com/oauth/"
TOKEN_URL = f"{API_BASE}/oauth/token"
REDIRECT_URI = "http://localhost:9876/callback"
SCOPES = "boards:read,boards:write,pins:read,pins:write"

_TOKEN_FILE = CONFIG_DIR / "pinterest_token.json"


def _save_tokens(data: dict) -> None:
    _TOKEN_FILE.write_text(json.dumps(data, indent=2))


def _load_tokens() -> dict:
    if _TOKEN_FILE.exists():
        return json.loads(_TOKEN_FILE.read_text())
    return {}


def _get_app_credentials() -> tuple[str, str]:
    settings = load_settings()
    app_id = settings.get("pinterest_app_id", "")
    app_secret = settings.get("pinterest_app_secret", "")
    if not app_id or not app_secret:
        raise ValueError(
            "pinterest_app_id and pinterest_app_secret must be set in config/settings.json. "
            "Create an app at https://developers.pinterest.com/apps/"
        )
    return app_id, app_secret


def get_access_token() -> str:
    """Get a valid access token, refreshing if needed."""
    tokens = _load_tokens()
    access_token = tokens.get("access_token", "")
    if not access_token:
        raise ValueError("No Pinterest access token. Run: python -m agents pin auth")
    return access_token


def _refresh_token(refresh_token: str) -> dict | None:
    app_id, app_secret = _get_app_credentials()
    r = httpx.put(
        TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        auth=(app_id, app_secret),
        timeout=10,
    )
    if r.status_code == 200:
        data = r.json()
        tokens = _load_tokens()
        tokens["access_token"] = data["access_token"]
        if "refresh_token" in data:
            tokens["refresh_token"] = data["refresh_token"]
        _save_tokens(tokens)
        return tokens
    return None


def _api_call(method: str, url: str, token: str, **kwargs) -> httpx.Response:
    """Make an API call, refreshing the token once on 401."""
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    timeout = kwargs.pop("timeout", 15)
    r = httpx.request(method, url, headers=headers, timeout=timeout, **kwargs)

    if r.status_code == 401:
        tokens = _load_tokens()
        refresh = tokens.get("refresh_token", "")
        if refresh:
            new_tokens = _refresh_token(refresh)
            if new_tokens:
                headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
                r = httpx.request(method, url, headers=headers, timeout=timeout, **kwargs)

    return r


def run_oauth_flow() -> dict:
    """Run the full OAuth 2.0 authorization code flow."""
    app_id, app_secret = _get_app_credentials()
    state = secrets.token_urlsafe(16)

    auth_params = {
        "client_id": app_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    }
    auth_url = f"{AUTH_URL}?{urlencode(auth_params)}"

    captured = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            qs = parse_qs(urlparse(self.path).query)
            captured["code"] = qs.get("code", [None])[0]
            captured["state"] = qs.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorized! You can close this tab.</h2>")

        def log_message(self, *args):
            pass

    server = HTTPServer(("localhost", 9876), CallbackHandler)

    print("Opening browser for Pinterest authorization...")
    webbrowser.open(auth_url)

    server.handle_request()
    server.server_close()

    if captured.get("state") != state:
        raise ValueError("OAuth state mismatch — possible CSRF")
    code = captured.get("code")
    if not code:
        raise ValueError("No authorization code received")

    r = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        auth=(app_id, app_secret),
        timeout=15,
    )
    r.raise_for_status()
    tokens = r.json()
    _save_tokens(tokens)
    return tokens


def get_boards() -> list[dict]:
    """Fetch all boards for the authenticated user."""
    token = get_access_token()
    boards = []
    bookmark = None

    while True:
        params = {"page_size": 100}
        if bookmark:
            params["bookmark"] = bookmark

        r = _api_call("GET", f"{API_BASE}/boards", token, params=params)
        r.raise_for_status()
        data = r.json()
        boards.extend(data.get("items", []))
        bookmark = data.get("bookmark")
        if not bookmark:
            break

    return boards


def find_board_id(board_name: str) -> str | None:
    """Find a board ID by name (case-insensitive)."""
    boards = get_boards()
    for b in boards:
        if b["name"].lower() == board_name.lower():
            return b["id"]
    return None


def create_board(name: str, description: str = "") -> dict:
    """Create a new Pinterest board."""
    token = get_access_token()
    r = _api_call(
        "POST", f"{API_BASE}/boards", token,
        headers={"Content-Type": "application/json"},
        json={"name": name, "description": description, "privacy": "PUBLIC"},
    )
    r.raise_for_status()
    return r.json()


def _ensure_board(board_name: str) -> str:
    """Get or create a board, returning its ID."""
    board_id = find_board_id(board_name)
    if board_id:
        return board_id

    from agents.config import load_boards
    boards_config = load_boards()
    board_desc = ""
    for b in boards_config.get("boards", []):
        if b["name"].lower() == board_name.lower():
            board_desc = b.get("description", "")
            break

    board = create_board(board_name, board_desc)
    return board["id"]


def create_pin(
    image_path: Path,
    title: str,
    description: str,
    board_name: str,
    link: str,
) -> dict:
    """Create a pin on Pinterest via the API."""
    token = get_access_token()
    board_id = _ensure_board(board_name)

    # Read and encode image
    b64 = base64.b64encode(image_path.read_bytes()).decode()

    suffix = image_path.suffix.lower()
    content_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "image/png")

    payload = {
        "board_id": board_id,
        "title": title[:100],
        "description": description[:500],
        "link": link,
        "media_source": {
            "source_type": "image_base64",
            "content_type": content_type,
            "data": b64,
        },
    }

    r = _api_call(
        "POST", f"{API_BASE}/pins", token,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def check_token() -> dict | None:
    """Validate the current token. Returns info dict or None."""
    try:
        token = get_access_token()
    except ValueError:
        return None

    r = httpx.get(
        f"{API_BASE}/boards",
        headers={"Authorization": f"Bearer {token}"},
        params={"page_size": 1},
        timeout=10,
    )
    if r.status_code == 200:
        return {"status": "connected"}
    return None
