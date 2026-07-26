import requests
import traceback
from logger import get_logger

logger = get_logger()

class DiscordNotifier:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    def _send_embed(self, title: str, description: str, color: int):
        if not self.webhook_url:
            return

        embed = {
            "title": title,
            "description": description,
            "color": color
        }
        
        payload = {
            "embeds": [embed]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord webhook: {e}")

    def notify_success(self, video_id: str, yt_video_id: str, title: str):
        desc = f"Successfully uploaded **{title}** to YouTube!\n\n**TikTok ID**: {video_id}\n**YouTube URL**: https://youtube.com/watch?v={yt_video_id}"
        self._send_embed(title="✅ Video Uploaded Successfully", description=desc, color=0x00FF00)

    def notify_failure(self, video_id: str, title: str, reason: str, exception: Exception = None):
        desc = f"Failed to upload video **{title}** (ID: `{video_id}`) due to:\n**{reason}**"
        
        if exception:
            tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            # Discord limits descriptions to 4096 characters.
            if len(tb) > 2000:
                tb = tb[-2000:]
            desc += f"\n\n**Traceback**\n```python\n{tb}\n```"

        # Clamp the full description to Discord's embed limit.
        desc = desc[:4096]
        self._send_embed(title="❌ Video Upload Failed", description=desc, color=0xFF0000)

    def notify_exception(self, context: str, exception: Exception):
        desc = f"An unexpected error occurred during **{context}**."
        
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        if len(tb) > 2000:
            tb = tb[-2000:]
        desc += f"\n\n**Traceback**\n```python\n{tb}\n```"

        # Clamp the full description to Discord's embed limit.
        desc = desc[:4096]
        self._send_embed(title="⚠️ System Exception", description=desc, color=0xFFA500)
