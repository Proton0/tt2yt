"""
tt2yt: TikTok to YouTube Uploader

Copyright (C) 2026 Proton0

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

"""

import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = Path("secrets/token.json")


class YouTube:
    def __init__(self, client_secrets_file: str):
        self.client_secrets_file = client_secrets_file
        self.credentials = self._authenticate()
        self.youtube = build("youtube", "v3", credentials=self.credentials)

    def _authenticate(self) -> Credentials:
        print("Authenticating with Google")
        credentials = None

        if TOKEN_FILE.exists():
            credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("Access token expired, refreshing credentials")
                credentials.refresh(Request())
            else:
                print("\nLaunching browser window for Google auth")
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"Could not find client_secrets file at: {self.client_secrets_file}. "
                        f"Please download it from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                credentials = flow.run_local_server(port=0)

            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_FILE, "w") as token:
                token.write(credentials.to_json())
            print("Session saved successfully.")
        print("Authenticated successfully!")
        return credentials

    def upload_video(self, file_path: str, title: str, description: str = "") -> str | None:
        print("Preparing to upload video")
        if "#shorts" not in title.lower():
            title = f"{title} #shorts"

        body = {
            "snippet": {
                "title": title[:100],  # YouTube Max Title limit restriction
                "description": description or "#shorts #techtok #technology #tech",
                "categoryId": "28"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(file_path, chunksize=1024 * 1024, resumable=True)

        try:
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Uploading progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            print(f"Upload complete, Video ID assigned: {video_id}")
            return video_id

        except Exception as e:
            print(f"Exception : {e}", file=sys.stderr)
            return None


if __name__ == "__main__":
    try:
        uploader = YouTube("secrets/client_secrets.json")
        print("YouTube authenticated successfully")
    except Exception as err:
        print(f"Initialization Failed: {err}")
