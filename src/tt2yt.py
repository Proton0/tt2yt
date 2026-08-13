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
import time
from pathlib import Path
import subprocess

from logger import get_logger
from openrouter import OpenRouter
from tiktok import TikTok
from tracker import UploadTracker
from youtube import YouTube
from discord_notifier import DiscordNotifier

logger = get_logger()


AUDIO_EXTENSIONS = ('.mp3', '.m4a', '.wav')

def get_git_data():
    try:
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()

        try:
            current_tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"]).decode("utf-8").strip()
        except subprocess.CalledProcessError:
            current_tag = "N/A"

        return commit_hash, branch_name, current_tag
    except Exception as e:
        logger.error(f"Failed to get git data: {e}")
        return None, None, None

class TT2YT:
    def __init__(self, secrets: dict, client_secrets_file: str):
        self.secrets = secrets
        self.youtube = YouTube(client_secrets_file)
        self.tiktok = TikTok(secrets.get("tiktok_profile"), secrets.get("tiktok_channel_id"))
        self.tracker = UploadTracker()
        self.openrouter = OpenRouter(secrets['openrouter_key'])
        self.discord = DiscordNotifier(secrets.get('discord_webhook_url'), secrets=self.secrets)

        commit_hash, branch_name, current_tag = get_git_data()
        logger.info(f"tt2yt: YouTube Uploader for TikTok videos (version: {current_tag}, commit: {commit_hash}, branch: {branch_name})")

        if branch_name == "experimental":
            logger.warning("Alert: You are running the experimental branch. This may be unstable and is not really recommended to use!")


    def run(self):
        while True:
            try:
                videos = self.tiktok.get_videos()
                if not videos:
                    logger.info("No videos found")
                else:
                    for video in reversed(videos):
                        video_id = video["id"]

                        if self.tracker.is_uploaded(video_id):
                            continue

                        if self.tracker.is_recently_failed(video_id):
                            logger.info(f"Skipping {video_id} as it recently failed to upload (within 24h)")
                            continue

                        logger.info(f"Processing video: {video_id}")
                        title = video.get("title") or f"TikTok Video {video_id}"
                        downloaded_file = self.tiktok.download_video(video_id)

                        if not downloaded_file or not os.path.exists(downloaded_file):
                            logger.error(f"Failed to download {video_id}")
                            self.tracker.mark_as_failed(video_id)
                            self.discord.notify_failure(video_id, title, "Download failed or returned empty file")
                            continue

                        if Path(downloaded_file).suffix.lower() in AUDIO_EXTENSIONS:
                            logger.info(f"Skipping {video_id} as its a slideshow/photo!")
                            try:
                                os.remove(downloaded_file)
                            except Exception as e:
                                logger.error(f"Failed to delete slideshow file {downloaded_file}: {e}")
                            continue

                        if "tiktok-only" in title.lower():
                            logger.info(f"Skipping {video_id} because it has the tiktok-only tag")
                            try:
                                if downloaded_file and os.path.exists(downloaded_file):
                                    os.remove(downloaded_file)
                            except Exception as e:
                                logger.error(f"Failed to delete tiktok-only file {downloaded_file}: {e}")
                            continue

                        try:
                            desc = None
                            if self.openrouter.api_key:
                                desc = self.openrouter.generate_description(video.get("title") or "")

                            if not desc:
                                desc = video.get("title") or ""

                            yt_video_id = self.youtube.upload_video(downloaded_file, title, desc)

                            if yt_video_id:
                                self.tracker.mark_as_uploaded(video_id, yt_video_id)
                                logger.info(f"Uploaded tiktok video {video_id} to youtube ({yt_video_id})")
                                self.discord.notify_success(video_id, yt_video_id, title)
                            else:
                                self.tracker.mark_as_failed(video_id)
                                logger.error(f"Failed to upload {downloaded_file}")
                                self.discord.notify_failure(video_id, title, "YouTube upload returned None")

                        except Exception as e:
                            self.tracker.mark_as_failed(video_id)
                            self.discord.notify_failure(video_id, title, "Exception during YouTube upload", e)


                        finally:
                            try:
                                if os.path.exists(downloaded_file):
                                    os.remove(downloaded_file)
                            except Exception as e:
                                logger.error(f"Failed to delete video {downloaded_file}: {e}")

            except Exception as e:
                logger.error(f"Unhandled exception: {e}")
                self.discord.notify_exception("main loop", e)
            logger.info("Finished, sleeping now")
            time.sleep(1800)
