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
from requests.exceptions import RequestException, Timeout, ConnectionError as ReqConnectionError

from openrouter import OpenRouter


class TestAPIKeyAbuse:

    def test_none_api_key(self):
        client = OpenRouter(api_key=None)
        result = client.generate_description("Test Title")
        assert result is None

    def test_whitespace_only_api_key(self):
        client = OpenRouter(api_key="   ")
        with patch("requests.post", side_effect=RequestException("Invalid key")):
            result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_extremely_long_api_key(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated!"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="sk-" + "a" * 10000)
        result = client.generate_description("Test")
        assert result == "Generated!"


class TestTitleInputAbuse:

    @patch("requests.post")
    def test_empty_title(self, mock_post):
        """Empty string title."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "A description for nothing"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("")
        assert result == "A description for nothing"

    @patch("requests.post")
    def test_massive_title(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Brief desc"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("A" * 100000)
        assert result == "Brief desc"
        # Verify the massive title was included in the request
        payload = mock_post.call_args[1]["json"]
        assert "A" * 100000 in payload["messages"][1]["content"]

    @patch("requests.post")
    def test_emoji_spam_title(self, mock_post):
        """5000 emoji characters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Emoji vibes"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("🔥💀" * 5000)
        assert result == "Emoji vibes"

    @patch("requests.post")
    def test_null_bytes_in_title(self, mock_post):
        """Null bytes in title."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Handled"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("\x00\x01\x02")
        assert result == "Handled"

    @patch("requests.post")
    def test_html_injection_title(self, mock_post):
        """HTML/script injection in title."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Safe desc"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description('<script>alert("xss")</script>')
        assert result == "Safe desc"


class TestMalformedResponses:

    @patch("requests.post")
    def test_missing_content_key(self, mock_post):
        """Response has message but no 'content'."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_none_content(self, mock_post):
        """Content is explicitly None."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": None}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_no_message_key(self, mock_post):
        """Choice exists but has no 'message'."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_completely_wrong_structure(self, mock_post):
        """Response has no 'choices' key at all."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "structure"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_empty_string_content(self, mock_post):
        """Content is empty string → strip returns ''."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result == ""

    @patch("requests.post")
    def test_whitespace_only_content(self, mock_post):
        """Content is only whitespace → strip returns ''."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": " \n\t "}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result == ""

    @patch("requests.post")
    def test_choices_is_not_a_list(self, mock_post):
        """'choices' is a string instead of a list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": "not a list"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_response_json_raises_value_error(self, mock_post):
        """Response body is not JSON at all."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("No JSON in response")
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None



class TestHTTPErrors:
    """Test specific HTTP failure modes."""

    @patch("requests.post")
    def test_timeout_error(self, mock_post):
        """Request times out."""
        mock_post.side_effect = Timeout("Request timed out after 15s")

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_connection_error(self, mock_post):
        """DNS resolution failure or network unreachable."""
        mock_post.side_effect = ReqConnectionError("Failed to resolve host")

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_http_429_rate_limited(self, mock_post):
        """API returns 429 Too Many Requests."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = RequestException("429 Too Many Requests")
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_http_500_server_error(self, mock_post):
        """API returns 500 Internal Server Error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = RequestException("500 Internal Server Error")
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None

    @patch("requests.post")
    def test_http_503_service_unavailable(self, mock_post):
        """API returns 503 Service Unavailable."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = RequestException("503 Service Unavailable")
        mock_post.return_value = mock_response

        client = OpenRouter(api_key="fake-key")
        result = client.generate_description("Test")
        assert result is None
