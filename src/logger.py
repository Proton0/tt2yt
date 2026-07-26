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


from datetime import datetime
import logging
import os
import sys

logger = logging.getLogger("tt2yt")

def setup_logger(log_dir="logs", level=logging.INFO):
    """Configures the global tt2yt logger handlers."""
    os.makedirs(log_dir, exist_ok=True)

    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    logger.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"tt2yt-{timestamp}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def get_logger():
    """Retrieves the global tt2yt logger instance."""
    return logging.getLogger("tt2yt")