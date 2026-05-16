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
import time

from openrouter import OpenRouter
from tiktok import TikTok
from tracker import UploadTracker
from youtube import YouTube


class TT2YT:
    def __init__(self, secrets: dict, client_secrets_file: str):
        self.secrets = secrets
        self.youtube = YouTube(client_secrets_file)
        self.tiktok = TikTok(secrets['tiktok_profile'])
        self.tracker = UploadTracker()
        self.openrouter = OpenRouter(secrets['openrouter_key'])

    def run(self):
        while True:
            try:
                videos = self.tiktok.get_videos()
                if not videos:
                    print("No videos found")
                else:
                    for video in reversed(videos):
                        video_id = video["id"]

                        if self.tracker.is_uploaded(video_id):
                            continue

                        print(f"Processing video: {video_id}")
                        downloaded_file = self.tiktok.download_video(video_id)

                        if not downloaded_file or not os.path.exists(downloaded_file):
                            print(f"Failed to download {video_id}")
                            continue

                        title = video.get("title") or f"TikTok Video {video_id}"

                        try:
                            desc = self.openrouter.generate_description(video["title"])
                            yt_video_id = self.youtube.upload_video(downloaded_file, title, desc)

                            if yt_video_id:
                                self.tracker.mark_as_uploaded(video_id, yt_video_id)
                                print(f"Uploaded tiktok video {video_id} to youtube ({yt_video_id})")
                            else:
                                print(f"Failed to upload {downloaded_file}")

                        finally:
                            try:
                                if os.path.exists(downloaded_file):
                                    os.remove(downloaded_file)
                            except Exception as e:
                                print(f"Failed to delete video {downloaded_file}: {e}")

            except Exception as e:
                print(f"Unhandled exception: {e}", file=sys.stderr)
            print("Finished, sleeping now")
            time.sleep(1800)
