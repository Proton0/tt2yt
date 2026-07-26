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

def test_tiktok_init_empty():
    with pytest.raises(ValueError, match="Both tiktok_profile and tiktok_channel_id are None."):
        TikTok()
    
    with pytest.raises(ValueError, match="Both tiktok_profile and tiktok_channel_id are empty"):
        TikTok(tiktok_profile="", tiktok_channel_id="")

def test_tiktok_profile_parsing():
    scraper1 = TikTok("https://tiktok.com/vproton0")
    assert scraper1.tiktok_profile == "vproton0"
    
    scraper2 = TikTok("@vproton0")
    assert scraper2.tiktok_profile == "vproton0"

@patch("tiktok.YoutubeDL")
def test_tiktok_get_videos_channel_id(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = {
        'entries': [{'id': '456', 'url': 'http...', 'title': 'Test 2', 'duration': 10}]
    }
    
    scraper = TikTok(tiktok_channel_id="channel123")
    videos = scraper.get_videos()
    assert len(videos) == 1
    assert videos[0]['id'] == '456'
    mock_ydl_instance.extract_info.assert_called_with("tiktokuser:channel123", download=False)

@patch("tiktok.YoutubeDL")
def test_tiktok_get_videos_no_data(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = None
    
    scraper = TikTok("vproton0")
    assert scraper.get_videos() == []
    
    mock_ydl_instance.extract_info.return_value = {}
    assert scraper.get_videos() == []

@patch("tiktok.YoutubeDL")
def test_tiktok_get_videos_none_entry(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.return_value = {'entries': [None, {'id': '789'}]}
    
    scraper = TikTok("vproton0")
    videos = scraper.get_videos()
    assert len(videos) == 1
    assert videos[0]['id'] == '789'

@patch("tiktok.YoutubeDL")
def test_tiktok_get_videos_exception(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.side_effect = Exception("Extract failed")
    
    scraper = TikTok("vproton0")
    assert scraper.get_videos() == []

@patch("tiktok.YoutubeDL")
@patch("pathlib.Path.mkdir")
def test_tiktok_download_video_success(mock_mkdir, mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.prepare_filename.return_value = "downloads/123.mp4"
    
    scraper = TikTok("vproton0")
    filename = scraper.download_video("123")
    
    assert filename == "downloads/123.mp4"
    mock_mkdir.assert_called_once()
    mock_ydl_instance.extract_info.assert_called_once()

@patch("tiktok.YoutubeDL")
def test_tiktok_download_video_exception(mock_ydl_class):
    mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
    mock_ydl_instance.extract_info.side_effect = Exception("Download failed")
    
    scraper = TikTok("vproton0")
    assert scraper.download_video("123") is None