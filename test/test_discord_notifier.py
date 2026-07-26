import pytest
from unittest.mock import patch, MagicMock
from discord_notifier import DiscordNotifier

def test_no_webhook_url():
    notifier = DiscordNotifier(webhook_url=None)
    with patch("requests.post") as mock_post:
        notifier.notify_success("vid123", "yt123", "Test Title")
        mock_post.assert_not_called()

@patch("requests.post")
def test_notify_success(mock_post):
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    notifier.notify_success("vid123", "yt123", "Test Title")
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["embeds"][0]["title"] == "✅ Video Uploaded Successfully"
    assert "vid123" in kwargs["json"]["embeds"][0]["description"]
    assert "yt123" in kwargs["json"]["embeds"][0]["description"]
    assert kwargs["json"]["embeds"][0]["color"] == 0x00FF00

@patch("requests.post")
def test_notify_failure_no_exception(mock_post):
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    notifier.notify_failure("vid123", "Test Title", "Reason here")
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["embeds"][0]["title"] == "❌ Video Upload Failed"
    assert "Reason here" in kwargs["json"]["embeds"][0]["description"]
    assert "Traceback" not in kwargs["json"]["embeds"][0]["description"]
    assert kwargs["json"]["embeds"][0]["color"] == 0xFF0000

@patch("requests.post")
def test_notify_failure_with_exception(mock_post):
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    try:
        1 / 0
    except Exception as e:
        notifier.notify_failure("vid123", "Test Title", "Exception occurred", e)
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["embeds"][0]["title"] == "❌ Video Upload Failed"
    assert "Traceback" in kwargs["json"]["embeds"][0]["description"]
    assert "ZeroDivisionError" in kwargs["json"]["embeds"][0]["description"]

@patch("requests.post")
def test_notify_exception(mock_post):
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    try:
        raise ValueError("Something went wrong")
    except Exception as e:
        notifier.notify_exception("main loop", e)
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["embeds"][0]["title"] == "⚠️ System Exception"
    assert "main loop" in kwargs["json"]["embeds"][0]["description"]
    assert "ValueError" in kwargs["json"]["embeds"][0]["description"]

@patch("requests.post")
def test_request_exception_handled(mock_post, caplog):
    import requests
    mock_post.side_effect = requests.exceptions.RequestException("Discord down")
    
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    notifier.notify_success("vid", "yt", "Title")
    
    assert "Failed to send Discord webhook" in caplog.text
