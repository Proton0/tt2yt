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


import pytest
import argparse
from unittest.mock import patch

import main

def test_main_execution():
    with patch("sys.argv", ["main.py", "-tc", "channel123", "-c", "dummy.json"]), \
         patch("main.parse_secrets") as mock_parse, \
         patch("main.TT2YT") as mock_tt2yt:
        mock_parse.return_value = {"tiktok_channel_id": "channel123"}
        main.main()
        mock_parse.assert_called_once()
        mock_tt2yt.assert_called_once()
        mock_tt2yt.return_value.run.assert_called_once()

@patch('main.logger')
def test_main_runtime_error(mock_logger):
    with patch("sys.argv", ["main.py"]), \
         patch("main.parse_secrets", side_effect=RuntimeError("Test error")):
        with pytest.raises(SystemExit) as excinfo:
            main.main()
        assert excinfo.value.code == 1
        mock_logger.critical.assert_called_once_with("Fatal Error: Test error")
