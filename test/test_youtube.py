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
    # Bypass __init__ to avoid google oauth
    return YouTube.__new__(YouTube)


def test_process_title_500char(yt):
    title = "A" * 500
    result = yt._process_title(title)

    assert len(result) == 100
    assert result.endswith(" #shorts")
    assert result == ("A" * 92) + " #shorts"


def test_process_title_1000char(yt):
    title = "B" * 1000
    result = yt._process_title(title)

    assert len(result) == 100
    assert result.endswith(" #shorts")
    assert result == ("B" * 92) + " #shorts"


def test_process_title_30char(yt):
    title = "C" * 30
    result = yt._process_title(title)

    assert len(result) == 38
    assert result.endswith(" #shorts")
    assert result == ("C" * 30) + " #shorts"


def test_process_title_0char(yt):
    title = ""
    result = yt._process_title(title)

    assert result == " #shorts"


def test_process_title_50char(yt):
    title = "D" * 50
    result = yt._process_title(title)

    assert len(result) == 58
    assert result.endswith(" #shorts")
    assert result == ("D" * 50) + " #shorts"


def test_process_title_50char_caps(yt):
    base_title = "E" * 42
    title = base_title + " #SHORTS"
    result = yt._process_title(title)

    assert result == title
    assert len(result) == 50
    assert result.endswith(" #SHORTS")

@patch("youtube.TOKEN_FILE")
def test_youtube_missing_secrets(mock_token_file):
    mock_token_file.exists.return_value = False

    with pytest.raises(FileNotFoundError, match="Could not find client_secrets file"):
        YouTube("does_not_exist.json")

@patch("youtube.build")
@patch("youtube.YouTube._authenticate")
def test_youtube_init_success(mock_auth, mock_build):
    mock_auth.return_value = "mock_creds"
    yt = YouTube("dummy.json")
    mock_build.assert_called_once_with("youtube", "v3", credentials="mock_creds")

@patch("youtube.os.path.exists")
@patch("youtube.os.remove")
@patch("youtube.build")
@patch("youtube.YouTube._authenticate")
def test_youtube_init_refresh_error(mock_auth, mock_build, mock_remove, mock_exists):
    from google.auth.exceptions import RefreshError
    mock_auth.side_effect = RefreshError("Token expired")
    mock_exists.return_value = True
    
    with pytest.raises(RefreshError):
        YouTube("dummy.json")
        
    mock_remove.assert_called_once_with("secrets/token.json")

@patch("youtube.TOKEN_FILE")
@patch("youtube.Credentials.from_authorized_user_file")
def test_authenticate_valid_credentials(mock_from_file, mock_token_file, yt):
    mock_token_file.exists.return_value = True
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_from_file.return_value = mock_creds
    
    creds = yt._authenticate()
    assert creds == mock_creds

@patch("youtube.TOKEN_FILE")
@patch("youtube.Credentials.from_authorized_user_file")
@patch("youtube.Request")
def test_authenticate_expired_credentials_refresh(mock_request, mock_from_file, mock_token_file, yt):
    mock_token_file.exists.return_value = True
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = True
    mock_from_file.return_value = mock_creds
    
    with patch("builtins.open", mock_open()):
        creds = yt._authenticate()
        
    mock_creds.refresh.assert_called_once()
    assert creds == mock_creds

@patch("youtube.TOKEN_FILE")
@patch("youtube.os.path.exists")
@patch("youtube.InstalledAppFlow.from_client_secrets_file")
def test_authenticate_no_credentials_flow(mock_flow_from_file, mock_exists, mock_token_file, yt):
    mock_token_file.exists.return_value = False
    mock_exists.return_value = True
    
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = MagicMock(to_json=lambda: '{"token": "test"}')
    mock_flow_from_file.return_value = mock_flow
    
    yt.client_secrets_file = "dummy.json"
    
    with patch("builtins.open", mock_open()) as mock_file:
        creds = yt._authenticate()
        
    mock_flow.run_local_server.assert_called_once_with(port=0, open_browser=False)
    
    handle = mock_file()
    handle.write.assert_called_once_with('{"token": "test"}')

@patch("youtube.MediaFileUpload")
def test_upload_video_success(mock_media, yt):
    yt.youtube = MagicMock()
    mock_request = MagicMock()
    
    mock_status = MagicMock()
    mock_status.progress.return_value = 0.5
    
    mock_request.next_chunk.side_effect = [
        (mock_status, None),
        (None, {"id": "yt_12345"})
    ]
    yt.youtube.videos().insert.return_value = mock_request
    
    video_id = yt.upload_video("dummy.mp4", "Test Video", "Test Description")
    
    assert video_id == "yt_12345"
    yt.youtube.videos().insert.assert_called_once()
    mock_request.next_chunk.assert_called()

@patch("youtube.MediaFileUpload")
@patch("youtube.logger")
def test_upload_video_exception(mock_logger, mock_media, yt):
    yt.youtube = MagicMock()
    yt.youtube.videos().insert.side_effect = Exception("API Error")
    
    video_id = yt.upload_video("dummy.mp4", "Test Video", "")
    
    assert video_id is None
    mock_logger.error.assert_called_once_with("Exception : API Error")