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
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException

from openrouter import OpenRouter

def test_missing_api_key(capsys):
    client = OpenRouter(api_key="")
    result = client.generate_description("Test Title")

    assert result is None
    captured = capsys.readouterr()
    assert "OpenRouter API key is missing" in captured.err


@patch("requests.post")
def test_successful_description_generation(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "   This is a viral description!   "}}
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    client = OpenRouter(api_key="fake-sk-or-12345")
    result = client.generate_description("Test Title")

    assert result == "This is a viral description!"
    mock_post.assert_called_once()


@patch("requests.post")
def test_network_failure_returns_none(mock_post):
    mock_post.side_effect = RequestException("Connection timeout")

    client = OpenRouter(api_key="fake-sk-or-12345")
    result = client.generate_description("Test Title")

    assert result is None


@patch("requests.post")
def test_malformed_json_response_returns_none(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": []}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    client = OpenRouter(api_key="fake-api")
    result = client.generate_description("Test Title")

    assert result is None