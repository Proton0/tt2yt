import os
import sys
import time
import subprocess
import threading

import requests
from packaging.version import Version
import yt_dlp

from logger import get_logger

logger = get_logger()


class Updater:
    def __init__(self, interval=43200):
        self.interval = interval

    def get_latest_version(self):
        try:
            response = requests.get(
                "https://pypi.org/pypi/yt-dlp/json",
                timeout=10
            )
            response.raise_for_status()

            return response.json()["info"]["version"]

        except Exception as e:
            logger.warning(f"[Updater] Failed to check PyPI: {e}")
            return None

    def update(self):
        current = Version(yt_dlp.version.__version__)
        latest = self.get_latest_version()

        if not latest:
            return

        latest = Version(latest)

        if latest <= current:
            logger.info(f"[Updater] yt-dlp is up to date ({current})")
            return

        logger.info(f"[Updater] Updating yt-dlp {current} -> {latest}")

        try:
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "yt-dlp"
            ])

            logger.info("[Updater] Update successful, restarting...")
            self.restart()

        except subprocess.CalledProcessError:
            logger.error("[Updater] Update failed")

    def restart(self):
        os.execv(
            sys.executable,
            [sys.executable] + sys.argv
        )

    def run(self):
        while True:
            self.update()
            time.sleep(self.interval)


def start_updater():
    updater = Updater()

    thread = threading.Thread(
        target=updater.run,
        daemon=True
    )

    thread.start()

if __name__ == "__main__":
    start_updater()
    time.sleep(300)