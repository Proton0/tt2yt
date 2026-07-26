"""
tt2yt: TikTok to YouTube Uploader tests for logger.py
"""

import logging
import sys
from unittest.mock import patch, MagicMock
from logger import setup_logger, get_logger

def test_setup_logger_stream_routing(tmp_path):
    log_dir = tmp_path / "logs"
    
    # Reset logger handlers for test isolation
    logger = get_logger()
    logger.handlers.clear()

    setup_logger(log_dir=str(log_dir), level=logging.DEBUG)
    
    stdout_handler = None
    stderr_handler = None
    for h in logger.handlers:
        if isinstance(h, logging.StreamHandler) and not hasattr(h, "baseFilename"):
            if h.stream == sys.stdout:
                stdout_handler = h
            elif h.stream == sys.stderr:
                stderr_handler = h

    file_handler = None
    for h in logger.handlers:
        if isinstance(h, logging.FileHandler):
            file_handler = h

    assert stdout_handler is not None
    assert stderr_handler is not None
    assert stderr_handler.level == logging.ERROR
    assert file_handler is not None
    assert "tt2yt-" in file_handler.baseFilename
    assert file_handler.baseFilename.endswith(".log")
