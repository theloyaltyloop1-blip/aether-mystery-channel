"""Run this once to complete the YouTube OAuth login. Opens your browser,
you sign into the Google account that owns (or will own) the channel, grant
access, and a token.json is cached so the dashboard never asks again."""
from upload_youtube import get_credentials

if __name__ == "__main__":
    get_credentials()
    print("Login successful - token.json saved. You will not need to sign in again.")
