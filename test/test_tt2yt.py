import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
import os
from tt2yt import TT2YT, get_git_data


@patch("subprocess.check_output")
def test_get_git_data_failure(mock_subprocess):
    # Simulate git command not working
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "git")

    commit, branch, tag = get_git_data()
    assert commit is None
    assert branch is None
    assert tag is None


@patch("tt2yt.get_git_data")
@patch("tt2yt.YouTube")
@patch("tt2yt.TikTok")
@patch("tt2yt.OpenRouter")
@patch("tt2yt.UploadTracker")
def test_experimental_branch_warning(mock_tracker, mock_or, mock_tiktok, mock_yt, mock_git_data):
    # Force branch to experimental to trigger the alert log
    mock_git_data.return_value = ("abc1234", "experimental", "v1.0.0")

    secrets = {"tiktok_profile": "vproton0", "openrouter_key": "fake_key"}
    app = TT2YT(secrets, "dummy_client.json")

    assert app is not None



@patch("tt2yt.time.sleep")
@patch("tt2yt.YouTube")
@patch("tt2yt.TikTok")
@patch("tt2yt.OpenRouter")
@patch("tt2yt.UploadTracker")
def test_run_skips_already_uploaded(mock_tracker, mock_or, mock_tiktok, mock_yt, mock_sleep):
    mock_sleep.side_effect = StopIteration

    mock_tiktok.return_value.get_videos.return_value = [{"id": "vid_done", "title": "Old Video"}]
    mock_tracker.return_value.is_uploaded.return_value = True  # Already done!

    app = TT2YT({"tiktok_profile": "vproton0", "openrouter_key": "key"}, "dummy.json")

    with pytest.raises(StopIteration):
        app.run()

    # ensure it didnt download
    mock_tiktok.return_value.download_video.assert_not_called()


@patch("tt2yt.time.sleep")
@patch("tt2yt.os.path.exists")
@patch("tt2yt.YouTube")
@patch("tt2yt.TikTok")
@patch("tt2yt.OpenRouter")
@patch("tt2yt.UploadTracker")
def test_run_skips_tiktok_only_tag(mock_tracker, mock_or, mock_tiktok, mock_yt, mock_exists, mock_sleep):
    mock_sleep.side_effect = StopIteration

    mock_tiktok.return_value.get_videos.return_value = [{"id": "vid_exclusive", "title": "My Video (tiktok-only)"}]
    mock_tracker.return_value.is_uploaded.return_value = False
    mock_exists.return_value = True
    mock_tiktok.return_value.download_video.return_value = "downloads/vid_exclusive.mp4"

    app = TT2YT({"tiktok_profile": "vproton0", "openrouter_key": "key"}, "dummy.json")

    with pytest.raises(StopIteration):
        app.run()

    mock_or.return_value.generate_description.assert_not_called()
    mock_yt.return_value.upload_video.assert_not_called()


@patch("tt2yt.time.sleep")
@patch("tt2yt.os.path.exists")
@patch("tt2yt.YouTube")
@patch("tt2yt.TikTok")
@patch("tt2yt.OpenRouter")
@patch("tt2yt.UploadTracker")
def test_run_skips_audio_slideshow(mock_tracker, mock_or, mock_tiktok, mock_yt, mock_exists, mock_sleep):
    mock_sleep.side_effect = StopIteration

    mock_tiktok.return_value.get_videos.return_value = [{"id": "vid_audio", "title": "Photo slideshow"}]
    mock_tracker.return_value.is_uploaded.return_value = False
    mock_exists.return_value = True
    # Returns an audio extension instead of a video
    mock_tiktok.return_value.download_video.return_value = "downloads/vid_audio.mp3"

    app = TT2YT({"tiktok_profile": "vproton0", "openrouter_key": "key"}, "dummy.json")

    with pytest.raises(StopIteration):
        app.run()

    mock_yt.return_value.upload_video.assert_not_called()



@patch("tt2yt.time.sleep")
@patch("tt2yt.os.path.exists")
@patch("tt2yt.os.remove")
@patch("tt2yt.YouTube")
@patch("tt2yt.TikTok")
@patch("tt2yt.OpenRouter")
@patch("tt2yt.UploadTracker")
def test_run_openrouter_failure_falls_back_to_title(mock_tracker, mock_or, mock_tiktok, mock_yt, mock_remove, mock_exists, mock_sleep):
    mock_sleep.side_effect = StopIteration

    mock_tiktok.return_value.get_videos.return_value = [{"id": "vid123", "title": "Raw Title Only"}]
    mock_tracker.return_value.is_uploaded.return_value = False
    mock_exists.return_value = True
    mock_tiktok.return_value.download_video.return_value = "downloads/vid123.mp4"

    # mock openrouter failed
    mock_or.return_value.generate_description.return_value = None
    mock_yt.return_value.upload_video.return_value = "yt_id_999"

    app = TT2YT({"tiktok_profile": "vproton0", "openrouter_key": "key"}, "dummy.json")

    with pytest.raises(StopIteration):
        app.run()

    # verify it correctly just went back to raw title
    mock_yt.return_value.upload_video.assert_called_once_with(
        "downloads/vid123.mp4", "Raw Title Only", "Raw Title Only"
    )


@patch("tt2yt.time.sleep")
@patch("tt2yt.os.path.exists")
@patch("tt2yt.os.remove")
@patch("tt2yt.YouTube")
@patch("tt2yt.TikTok")
@patch("tt2yt.OpenRouter")
@patch("tt2yt.UploadTracker")
def test_run_handles_youtube_upload_failure(mock_tracker, mock_or, mock_tiktok, mock_yt, mock_remove, mock_exists, mock_sleep):
    mock_sleep.side_effect = StopIteration

    mock_tiktok.return_value.get_videos.return_value = [{"id": "vid123", "title": "Test"}]
    mock_tracker.return_value.is_uploaded.return_value = False
    mock_exists.return_value = True
    mock_tiktok.return_value.download_video.return_value = "downloads/vid123.mp4"

    # failed upload
    mock_yt.return_value.upload_video.return_value = None

    app = TT2YT({"tiktok_profile": "vproton0", "openrouter_key": "key"}, "dummy.json")

    with pytest.raises(StopIteration):
        app.run()

    # ensure it didnt mark it as uploaded AND it also deleted the file
    mock_tracker.return_value.mark_as_uploaded.assert_not_called()
    mock_remove.assert_called_once()


@patch("tt2yt.time.sleep")
@patch("tt2yt.YouTube")
@patch("tt2yt.TikTok")
@patch("tt2yt.OpenRouter")
@patch("tt2yt.UploadTracker")
def test_run_survives_unhandled_loop_exception(mock_tracker, mock_or, mock_tiktok, mock_yt, mock_sleep):
    mock_sleep.side_effect = [None, StopIteration]

    # force a fake exception
    mock_tiktok.return_value.get_videos.side_effect = Exception("TikTok API is down completely")

    app = TT2YT({"tiktok_profile": "vproton0", "openrouter_key": "key"}, "dummy.json")

    with pytest.raises(StopIteration):
        app.run()

    assert mock_sleep.call_count == 2