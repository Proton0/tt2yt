import pytest
from unittest.mock import patch, MagicMock

from tiktok import TikTok

@patch("tiktok.YoutubeDL")
def test_tiktok_get_videos_success(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value

    mock_ydl_instance.extract_info.return_value = {
        'entries': [
            {'id': '123', 'url': 'http...', 'title': 'Cool Project', 'duration': 15}
        ]
    }

    scraper = TikTok("vproton0")
    videos = scraper.get_videos()

    assert len(videos) == 1
    assert videos[0]['id'] == '123'
    assert videos[0]['title'] == 'Cool Project'