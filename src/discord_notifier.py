import re
import requests
import traceback
from logger import get_logger

logger = get_logger()

WIN_PATH_REGEX = r'(?<![a-zA-Z0-9_])[a-zA-Z]:[\\/](?:[^\\/:*?"<>|\r\n]+[\\/])*(?:[^\\/:*?"<>|\r\n]+)'
UNIX_PATH_REGEX = r'(?<![:/\w])/(?:[\w.-]+/)+[\w.-]*'
REL_PATH_REGEX = r'(?<![a-zA-Z0-9_])(?:\.|\.\.)[\\/](?:[\w.-]+[\\/])*(?:[\w.-]+)'
PATH_PATTERN = re.compile(f'({WIN_PATH_REGEX}|{UNIX_PATH_REGEX}|{REL_PATH_REGEX})')

class DiscordNotifier:
    def __init__(self, webhook_url: str = None, secrets: dict | list | set | str = None):
        self.webhook_url = webhook_url
        self.secrets = set()
        if secrets:
            self.set_secrets(secrets)

    def set_secrets(self, secrets):
        self.secrets = self._extract_secret_strings(secrets)

    def _extract_secret_strings(self, obj) -> set[str]:
        secret_set = set()
        if isinstance(obj, str):
            s = obj.strip()
            if s:
                secret_set.add(s)
        elif isinstance(obj, dict):
            for v in obj.values():
                secret_set.update(self._extract_secret_strings(v))
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                secret_set.update(self._extract_secret_strings(item))
        return secret_set

    def _redact(self, text: str) -> str:
        if not text or not isinstance(text, str):
            return text

        # Redact secrets
        for secret in sorted(self.secrets, key=len, reverse=True):
            if secret:
                text = text.replace(secret, "[REDACTED]")

        # Redact file paths
        text = PATH_PATTERN.sub("[REDACTED]", text)
        return text

    def _send_embed(self, title: str, description: str, color: int):
        if not self.webhook_url:
            return

        title = self._redact(title)
        description = self._redact(description)

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
