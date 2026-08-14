import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
BASE_DIR = os.path.dirname(__file__)
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "client_secret_kids.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token_kids.json")

if __name__ == "__main__":
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"Login successful - {TOKEN_FILE} saved.")
