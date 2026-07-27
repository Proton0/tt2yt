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
from unittest.mock import patch, MagicMock, mock_open
from youtube import YouTube


@pytest.fixture
def yt():
    """Bypass __init__ to avoid Google OAuth during testing."""
    return YouTube.__new__(YouTube)


# ---------------------------------------------------------------------------
# _process_title abuse
# ---------------------------------------------------------------------------

class TestProcessTitleAbuse:
    """Adversarial inputs to _process_title."""

    def test_single_char_title(self, yt):
        result = yt._process_title("a")
        assert result == "a #shorts"
        assert len(result) <= 100

    def test_all_spaces_title(self, yt):
        """200 spaces — should still append #shorts."""
        result = yt._process_title(" " * 200)
        assert "#shorts" in result.lower()
        assert len(result) <= 100

    def test_just_shorts_tag(self, yt):
        """Title is literally '#shorts' already."""
        result = yt._process_title("#shorts")
        assert result == "#shorts"
        assert len(result) <= 100

    def test_shorts_tag_lowercase(self, yt):
        result = yt._process_title("My Video #shorts")
        assert result == "My Video #shorts"

    def test_multiple_shorts_tags(self, yt):
        """Multiple #shorts variants in title."""
        result = yt._process_title("#SHORTS #shorts #Shorts")
        assert len(result) <= 100

    def test_shorts_tag_in_middle(self, yt):
        """#shorts appearing mid-title."""
        result = yt._process_title("Before #shorts After")
        assert result == "Before #shorts After"

    def test_all_emoji_long_title(self, yt):
        """200 emoji characters — multi-byte stress."""
        title = "🎵🔥" * 100
        result = yt._process_title(title)
        assert len(result) <= 100
        assert result.endswith(" #shorts")

    def test_control_characters_in_title(self, yt):
        """Tabs, newlines, carriage returns in title."""
        result = yt._process_title("\n\t\r Title With Controls \x00")
        assert "#shorts" in result.lower()

    def test_exactly_92_char_title(self, yt):
        """92 chars + ' #shorts' = exactly 100. Boundary check."""
        title = "X" * 92
        result = yt._process_title(title)
        assert len(result) == 100
        assert result == ("X" * 92) + " #shorts"

    def test_exactly_93_char_title(self, yt):
        """93 chars → should be truncated to 92 + ' #shorts' = 100."""
        title = "Y" * 93
        result = yt._process_title(title)
        assert len(result) == 100
        assert result == ("Y" * 92) + " #shorts"

    def test_exactly_100_char_title_without_shorts(self, yt):
        """100 chars with no #shorts → truncate to 92 + tag."""
        title = "Z" * 100
        result = yt._process_title(title)
        assert len(result) == 100
        assert result.endswith(" #shorts")

    def test_null_bytes_in_title(self, yt):
        """Null bytes should not crash processing."""
        result = yt._process_title("Title\x00With\x00Nulls")
        assert result is not None

    def test_rtl_text_title(self, yt):
        """Right-to-left Arabic text."""
        result = yt._process_title("مرحبا بالعالم")
        assert "#shorts" in result.lower()

    def test_title_with_only_hashtag_symbol(self, yt):
        result = yt._process_title("#")
        assert "#shorts" in result.lower()


# ---------------------------------------------------------------------------
# upload_video abuse
# ---------------------------------------------------------------------------

class TestUploadVideoAbuse:
    """Adversarial inputs to upload_video."""

    @patch("youtube.MediaFileUpload")
    @patch("youtube.logger")
    def test_upload_with_empty_strings(self, mock_logger, mock_media, yt):
        """All empty strings for upload parameters."""
        yt.youtube = MagicMock()
        yt.youtube.videos().insert.side_effect = Exception("Invalid request")

        result = yt.upload_video("", "", "")
        assert result is None

    @patch("youtube.MediaFileUpload")
    @patch("youtube.logger")
    def test_upload_massive_title_and_description(self, mock_logger, mock_media, yt):
        """10KB title and 50KB description."""
        yt.youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "yt_massive"})
        yt.youtube.videos().insert.return_value = mock_request

        result = yt.upload_video("test.mp4", "A" * 10000, "B" * 50000)
        assert result == "yt_massive"

    @patch("youtube.MediaFileUpload")
    def test_upload_chunked_partial_failure(self, mock_media, yt):
        """next_chunk raises mid-upload."""
        yt.youtube = MagicMock()
        mock_request = MagicMock()

        # First chunk OK, second chunk explodes
        mock_status = MagicMock()
        mock_status.progress.return_value = 0.25
        mock_request.next_chunk.side_effect = [
            (mock_status, None),
            Exception("Connection reset during upload"),
        ]
        yt.youtube.videos().insert.return_value = mock_request

        result = yt.upload_video("test.mp4", "Test", "Desc")
        assert result is None

    @patch("youtube.MediaFileUpload")
    def test_upload_response_missing_id(self, mock_media, yt):
        """YouTube returns a response with no 'id' key."""
        yt.youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"status": "ok"})  # No 'id'
        yt.youtube.videos().insert.return_value = mock_request

        result = yt.upload_video("test.mp4", "Test", "Desc")
        assert result is None  # response.get("id") returns None

    @patch("youtube.MediaFileUpload")
    def test_upload_with_no_description_uses_default(self, mock_media, yt):
        """Empty description should trigger default hashtags."""
        yt.youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {"id": "yt_default"})
        yt.youtube.videos().insert.return_value = mock_request

        yt.upload_video("test.mp4", "Test Title", "")

        call_args = yt.youtube.videos().insert.call_args
        body = call_args[1]["body"] if "body" in call_args[1] else call_args[0][0]
        # description should be the default hashtags since empty string is falsy
        assert body["snippet"]["description"] == "#shorts #techtok #technology #tech"


# ---------------------------------------------------------------------------
# Authentication abuse
# ---------------------------------------------------------------------------

class TestAuthAbuse:
    """Edge cases in authentication flow."""

    @patch("youtube.TOKEN_FILE")
    @patch("youtube.Credentials.from_authorized_user_file")
    def test_corrupt_token_file(self, mock_from_file, mock_token_file, yt):
        """Corrupted token.json → Credentials constructor raises."""
        mock_token_file.exists.return_value = True
        mock_from_file.side_effect = Exception("Invalid JSON in token file")

        with pytest.raises(Exception, match="Invalid JSON"):
            yt._authenticate()

    @patch("youtube.TOKEN_FILE")
    @patch("youtube.Credentials.from_authorized_user_file")
    def test_expired_no_refresh_token(self, mock_from_file, mock_token_file, yt):
        """Expired credentials with no refresh_token → triggers full OAuth flow."""
        mock_token_file.exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = None  # No refresh token!
        mock_from_file.return_value = mock_creds

        yt.client_secrets_file = "dummy.json"

        with patch("youtube.os.path.exists", return_value=True), \
             patch("youtube.InstalledAppFlow.from_client_secrets_file") as mock_flow, \
             patch("builtins.open", mock_open()):
            mock_flow_instance = MagicMock()
            mock_flow_instance.run_local_server.return_value = MagicMock(
                to_json=lambda: '{"token": "new"}'
            )
            mock_flow.return_value = mock_flow_instance

            creds = yt._authenticate()

        mock_flow_instance.run_local_server.assert_called_once()

    @patch("youtube.TOKEN_FILE")
    @patch("youtube.Credentials.from_authorized_user_file")
    @patch("youtube.Request")
    def test_refresh_raises_exception(self, mock_request, mock_from_file, mock_token_file, yt):
        """credentials.refresh() raises an exception."""
        mock_token_file.exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "valid_refresh"
        mock_creds.refresh.side_effect = Exception("Network error during refresh")
        mock_from_file.return_value = mock_creds

        with pytest.raises(Exception, match="Network error during refresh"):
            yt._authenticate()
