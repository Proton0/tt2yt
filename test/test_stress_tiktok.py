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
from pathlib import Path

from tiktok import TikTok




class TestTikTokInitAbuse:

    def test_whitespace_only_profile(self):
        t = TikTok("   ")
        assert t.tiktok_profile is None or t.tiktok_profile == ""

    def test_tab_newline_profile(self):
        t = TikTok("\t\n")
        assert t.tiktok_profile is None or t.tiktok_profile == ""

    def test_just_at_sign(self):
        t = TikTok("@")
        assert t.tiktok_profile == ""

    def test_multiple_at_signs(self):
        t = TikTok("@@username")
        assert t.tiktok_profile == "username"

    def test_extremely_long_profile(self):
        long_name = "a" * 10000
        t = TikTok(long_name)
        assert t.tiktok_profile == long_name

    def test_unicode_cjk_profile(self):
        t = TikTok("https://tiktok.com/@用户名")
        assert "用户名" in (t.tiktok_profile or "")

    def test_emoji_in_profile(self):
        t = TikTok("@user🎵name")
        assert t.tiktok_profile is not None

    def test_url_with_path_traversal(self):
        t = TikTok("https://tiktok.com/@user/../../../etc/passwd")
        assert t.tiktok_profile is not None
        assert t.tiktok_profile == "user"

    def test_wrong_domain_url(self):
        t = TikTok("https://evil.com/@malicious_user")
        # Contains "@" so regex path is taken
        assert t.tiktok_profile == "malicious_user"

    def test_url_with_null_bytes(self):
        t = TikTok("user\x00name")
        assert t.tiktok_profile is not None

    def test_profile_with_trailing_slash(self):
        t = TikTok("https://tiktok.com/@testuser///")
        assert t.tiktok_profile == "testuser"

    def test_both_profile_and_channel_id(self):
        t = TikTok("vproton0", "channel123")
        assert t.tiktok_profile == "vproton0"
        assert t.tiktok_channel_id == "channel123"

    def test_channel_id_with_special_chars(self):
        cid = "MS4wLjABAAAA_3nK1eKl6nn2JV3s2PJ95tUKmnORf"
        t = TikTok(None, cid)
        assert t.tiktok_channel_id == cid


class TestTikTokDownloadAbuse:

    def test_download_without_profile_raises(self):
        t = TikTok(None, "channel123")
        with pytest.raises(ValueError, match="Cannot download individual videos without a TikTok profile"):
            t.download_video("vid123")

    @patch("tiktok.YoutubeDL")
    @patch("pathlib.Path.mkdir")
    def test_download_empty_video_id(self, mock_mkdir, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.side_effect = Exception("Invalid video ID")

        t = TikTok("vproton0")
        result = t.download_video("")
        assert result is None

    @patch("tiktok.YoutubeDL")
    @patch("pathlib.Path.mkdir")
    def test_download_path_traversal_video_id(self, mock_mkdir, mock_ydl_class):
        """Path traversal in video_id should not escape downloads dir."""
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.side_effect = Exception("Not found")

        t = TikTok("vproton0")
        result = t.download_video("../../etc/passwd")
        assert result is None



class TestTikTokGetVideosAbuse:

    @patch("tiktok.YoutubeDL")
    def test_entries_with_missing_id(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'entries': [
                {'id': None, 'url': 'http://...', 'title': 'No ID Video'},
                {'url': 'http://...', 'title': 'Missing ID Key'},  # No 'id' at all
            ]
        }
        t = TikTok("vproton0")
        videos = t.get_videos()
        assert len(videos) == 2
        assert videos[0]['id'] is None
        assert videos[1]['id'] is None  # .get('id') returns None

    @patch("tiktok.YoutubeDL")
    def test_extremely_large_entries_list(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        entries = [{'id': str(i), 'url': f'http://{i}', 'title': f'Video {i}', 'duration': 10}
                   for i in range(1000)]
        mock_ydl_instance.extract_info.return_value = {'entries': entries}

        t = TikTok("vproton0")
        videos = t.get_videos()
        assert len(videos) == 1000

    @patch("tiktok.YoutubeDL")
    def test_entries_all_none(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'entries': [None, None, None]
        }
        t = TikTok("vproton0")
        videos = t.get_videos()
        assert videos == []

    @patch("tiktok.YoutubeDL")
    def test_entries_with_unicode_titles(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'entries': [
                {'id': '1', 'url': 'http://...', 'title': '🔥💀 مرحبا 你好 こんにちは', 'duration': 30},
            ]
        }
        t = TikTok("vproton0")
        videos = t.get_videos()
        assert len(videos) == 1
        assert '🔥' in videos[0]['title']

    @patch("tiktok.YoutubeDL")
    def test_extract_info_returns_empty_dict(self, mock_ydl_class):
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {}

        t = TikTok("vproton0")
        assert t.get_videos() == []
