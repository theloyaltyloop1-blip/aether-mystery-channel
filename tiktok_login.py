"""
AETHER - TikTok OAuth login (one-time)
TikTok's Content Posting API uses OAuth2 + PKCE, no ready-made Python SDK
like Google's, so this implements the flow directly: opens the consent
page in your browser, catches the redirect with a throwaway local HTTP
server, exchanges the code for tokens, and caches them in tiktok_token.json.

Run once: venv\\Scripts\\python tiktok_login.py
Requires tiktok_secrets.json (client_key + client_secret) already filled in,
and http://localhost:8921/ registered as a redirect URI in your TikTok
Developer app settings.
"""
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser

import requests

BASE_DIR = os.path.dirname(__file__)
SECRETS_FILE = os.path.join(BASE_DIR, "tiktok_secrets.json")
TOKEN_FILE = os.path.join(BASE_DIR, "tiktok_token.json")

REDIRECT_URI = "http://localhost:8921/"
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
SCOPES = "video.upload,user.info.basic"


def _load_secrets() -> dict:
    if not os.path.exists(SECRETS_FILE):
        raise SystemExit(
            f"Missing {SECRETS_FILE}. Copy tiktok_secrets.example.json to tiktok_secrets.json "
            "and fill in your client_key and client_secret from the TikTok Developer portal."
        )
    with open(SECRETS_FILE) as f:
        return json.load(f)


def _make_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:128]
    # TikTok's PKCE implementation deviates from RFC 7636 here: it wants the
    # SHA256 digest as a hex string, not base64url-encoded like every other
    # OAuth provider - using base64url (the "correct" way) fails token exchange.
    challenge = hashlib.sha256(verifier.encode()).hexdigest()
    return verifier, challenge


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    result = {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        _CallbackHandler.result["code"] = params.get("code", [None])[0]
        _CallbackHandler.result["state"] = params.get("state", [None])[0]
        _CallbackHandler.result["error"] = params.get("error", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        msg = "Login successful - you can close this tab." if _CallbackHandler.result.get("code") \
            else f"Login failed: {_CallbackHandler.result.get('error')}"
        self.wfile.write(f"<html><body><h2>{msg}</h2></body></html>".encode())

    def log_message(self, *args):
        pass  # silence default request logging


def _catch_redirect(expected_state: str) -> str:
    server = http.server.HTTPServer(("localhost", 8921), _CallbackHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout=180)

    result = _CallbackHandler.result
    if result.get("error"):
        raise SystemExit(f"TikTok login failed: {result['error']}")
    if not result.get("code"):
        raise SystemExit("Timed out waiting for TikTok login redirect.")
    if result.get("state") != expected_state:
        raise SystemExit("State mismatch - possible CSRF, aborting.")
    return result["code"]


def login() -> dict:
    secrets_data = _load_secrets()
    client_key = secrets_data["client_key"]
    client_secret = secrets_data["client_secret"]

    verifier, challenge = _make_pkce_pair()
    state = secrets.token_urlsafe(16)

    params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print(f"Opening browser for TikTok login:\n{auth_url}\n")
    webbrowser.open(auth_url)

    code = _catch_redirect(state)

    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier,
        },
        timeout=30,
    )
    resp.raise_for_status()
    token_data = resp.json()
    if "access_token" not in token_data:
        raise SystemExit(f"TikTok token exchange failed: {token_data}")

    token_data["obtained_at"] = time.time()
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    return token_data


if __name__ == "__main__":
    token_data = login()
    print("TikTok login successful - tiktok_token.json saved.")
    print(f"Scopes granted: {token_data.get('scope')}")
