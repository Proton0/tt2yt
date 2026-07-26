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

from pathlib import Path
import re
from yt_dlp import YoutubeDL

from logger import get_logger

logger = get_logger()

DOWNLOAD_DIR = Path("downloads")


class TikTok:
    def __init__(self, tiktok_profile: str | None = None, tiktok_channel_id: str | None = None):
        self.tiktok_profile = None
        self.tiktok_channel_id = tiktok_channel_id

        if tiktok_profile is None and tiktok_channel_id is None:
            raise ValueError("Both tiktok_profile and tiktok_channel_id are None.")

        if tiktok_profile == "" and tiktok_channel_id == "":
            raise ValueError("Both tiktok_profile and tiktok_channel_id are empty")

        if tiktok_profile:
            profile = tiktok_profile.strip()
            if "tiktok.com" in profile or "@" in profile:
                match = re.search(r'@([a-zA-Z0-9_\.]+)', profile)
                if match:
                    profile = match.group(1)
                else:
                    profile = profile.rstrip("/").split("/")[-1].lstrip("@")
            else:
                profile = profile.lstrip("@")
            self.tiktok_profile = profile

        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        }

    def get_videos(self) -> list[dict]:
        logger.info("Getting tiktok videos...")
        ydl_opts = {
            'extract_flat': True,
            'playlistend': 25,
            'skip_download': True,
            'quiet': True,
            'no_warnings': False,
            'http_headers': self.headers
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                if self.tiktok_profile:
                    profile_data = ydl.extract_info(f"https://tiktok.com/@{self.tiktok_profile}", download=False)
                else:
                    # use the channel id instead of username as yt-dlp recommends using channel id
                    profile_data = ydl.extract_info(f"tiktokuser:{self.tiktok_channel_id}", download=False)


                if not profile_data or 'entries' not in profile_data:
                    logger.warning("No videos found or failed to parse profile metadata.")
                    return []

                videos = []
                for entry in profile_data['entries']:
                    if not entry:
                        continue

                    videos.append({
                        'id': entry.get('id'),
                        'url': entry.get('url'),
                        'title': entry.get('title'),
                        'duration': entry.get('duration')
                    })

                return videos

        except Exception as e:
            logger.error(f"Error extracting TikTok profile data: {e}")
            return []

    def download_video(self, video_id: str) -> str | None:
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        video_url = f"https://www.tiktok.com/@{self.tiktok_profile}/video/{video_id}"
        output_template = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': False,
            'http_headers': self.headers
        }

        logger.info(f"Downloading video {video_id}...")

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                downloaded_file = ydl.prepare_filename(info)

                return downloaded_file

        except Exception as e:
            logger.error(
                f"Error downloading video {video_id}: {e}\n"
                "Is yt-dlp up-to-date? Please ensure its up-to-date before writing an issue"
            )
            return None


if __name__ == "__main__": # pragma: no cover
    logger.info("Using profile")
    scraper = TikTok("vproton0")
    latest_videos = scraper.get_videos()

    logger.info(f"Retrieved {len(latest_videos)} items:")
    for idx, vid in enumerate(latest_videos, 1):
        logger.info(f"{idx}. [{vid['id']}] -> {vid['title'][:40]}...")

    logger.info("Using channel ID")
    scraper_id = TikTok(None, "MS4wLjABAAAA_3nK1eKl6nn2JV3s2PJ95tUKmnORf_SXoGMBWyYRK8atwrEfuwbPOxGfSPD9fMGf")
    latest_vids = scraper_id.get_videos()

    logger.info(f"Retrieved {len(latest_vids)} items:")
    for idx, vid in enumerate(latest_vids, 1):
        logger.info(f"{idx}. [{vid['id']}] -> {vid['title'][:40]}...")
