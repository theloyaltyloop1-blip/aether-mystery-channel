"""
AETHER - TikTok uploader
Uses TikTok's Content Posting API (free, part of the TikTok for Developers
program). This app's Sandbox is only granted the video.upload scope (not
video.publish), which means it can only push videos to the account owner's
TikTok inbox as a draft - the account owner still has to open the TikTok app
and tap Post themselves. That's a TikTok platform restriction on unaudited
apps, not something this code can bypass. Once TikTok audits the app and
grants video.publish, direct/public posting becomes possible and this file
would need the /post/publish/video/init/ endpoint instead.
"""
import json
import os
import sys
import time

import requests

from tiktok_login import login, TOKEN_FILE, SECRETS_FILE

API_BASE = "https://open.tiktokapis.com/v2"


def _load_secrets() -> dict:
    with open(SECRETS_FILE) as f:
        return json.load(f)


def get_access_token() -> str:
    if not os.path.exists(TOKEN_FILE):
        return login()["access_token"]

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    expires_in = token_data.get("expires_in", 0)
    obtained_at = token_data.get("obtained_at", 0)
    if time.time() < obtained_at + expires_in - 120:
        return token_data["access_token"]

    # expired - refresh rather than re-running the interactive browser login
    secrets_data = _load_secrets()
    resp = requests.post(
        f"{API_BASE}/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": secrets_data["client_key"],
            "client_secret": secrets_data["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": token_data["refresh_token"],
        },
        timeout=30,
    )
    resp.raise_for_status()
    new_token = resp.json()
    if "access_token" not in new_token:
        # refresh token itself expired (long-lived, ~365 days) - fall back to interactive login
        return login()["access_token"]

    new_token["obtained_at"] = time.time()
    with open(TOKEN_FILE, "w") as f:
        json.dump(new_token, f, indent=2)
    return new_token["access_token"]


def upload_video(video_path: str, title: str) -> dict:
    access_token = get_access_token()
    video_size = os.path.getsize(video_path)

    init_resp = requests.post(
        f"{API_BASE}/post/publish/inbox/video/init/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()
    if init_data.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok init failed: {init_data['error']}")

    publish_id = init_data["data"]["publish_id"]
    upload_url = init_data["data"]["upload_url"]

    with open(video_path, "rb") as f:
        video_bytes = f.read()
    upload_resp = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
        },
        data=video_bytes,
        timeout=120,
    )
    upload_resp.raise_for_status()

    return {"publish_id": publish_id, "mode": "inbox_draft"}


def check_status(publish_id: str) -> dict:
    access_token = get_access_token()
    resp = requests.post(
        f"{API_BASE}/post/publish/status/fetch/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"publish_id": publish_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


if __name__ == "__main__":
    data = json.load(sys.stdin)
    result = upload_video(data["video_path"], data["title"])
    print(json.dumps(result, indent=2))
    print(
        "Note: sent to the TikTok inbox as a draft - open the TikTok app and tap Post to "
        "publish it. This app only has video.upload scope (not video.publish), which is "
        "TikTok's restriction on unaudited apps, not something this code controls.",
        file=sys.stderr,
    )
