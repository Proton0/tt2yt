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


@patch("requests.post")
def test_redact_secrets(mock_post):
    secrets = {
        "openrouter_key": "sk-or-v1-super-secret-key-12345",
        "tiktok_profile": "my_secret_user",
    }
    notifier = DiscordNotifier(webhook_url="http://fake.url", secrets=secrets)
    notifier._send_embed(title="Error sk-or-v1-super-secret-key-12345", description="failed with my_secret_user", color=0xFF0000)
    
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    desc = kwargs["json"]["embeds"][0]["description"]
    title = kwargs["json"]["embeds"][0]["title"]
    
    assert "sk-or-v1-super-secret-key-12345" not in title
    assert "my_secret_user" not in desc
    assert "[REDACTED]" in title
    assert "[REDACTED]" in desc


@patch("requests.post")
def test_redact_nested_secrets(mock_post):
    secrets = {
        "client_secrets": {
            "client_id": "google-client-id-123.apps.googleusercontent.com",
            "client_secret": "GOCSPX-secret_abc_123",
        }
    }
    notifier = DiscordNotifier(webhook_url="http://fake.url", secrets=secrets)
    notifier.notify_failure("vid123", "Upload error", "Failed using google-client-id-123.apps.googleusercontent.com and GOCSPX-secret_abc_123")
    
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    desc = kwargs["json"]["embeds"][0]["description"]
    
    assert "google-client-id-123.apps.googleusercontent.com" not in desc
    assert "GOCSPX-secret_abc_123" not in desc
    assert desc.count("[REDACTED]") >= 2


@patch("requests.post")
def test_redact_unix_paths(mock_post):
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    notifier.notify_failure("vid123", "Title", "Error at /home/user/project/main.py or /tmp/log.txt")
    
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    desc = kwargs["json"]["embeds"][0]["description"]
    
    assert "/home/user/project/main.py" not in desc
    assert "/tmp/log.txt" not in desc
    assert "[REDACTED]" in desc


@patch("requests.post")
def test_redact_windows_paths(mock_post):
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    notifier.notify_failure("vid123", "Title", r"Error at C:\Users\username\app\main.py or D:\data\file.txt")
    
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    desc = kwargs["json"]["embeds"][0]["description"]
    
    assert r"C:\Users\username\app\main.py" not in desc
    assert r"D:\data\file.txt" not in desc
    assert "[REDACTED]" in desc


@patch("requests.post")
def test_redact_relative_paths(mock_post):
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    notifier.notify_failure("vid123", "Title", "Error at ./src/main.py or ../config/settings.json")
    
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    desc = kwargs["json"]["embeds"][0]["description"]
    
    assert "./src/main.py" not in desc
    assert "../config/settings.json" not in desc
    assert "[REDACTED]" in desc


@patch("requests.post")
def test_preserve_urls(mock_post):
    notifier = DiscordNotifier(webhook_url="http://fake.url")
    notifier.notify_success("vid123", "yt123", "Test Title")
    
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    desc = kwargs["json"]["embeds"][0]["description"]
    
    assert "https://youtube.com/watch?v=yt123" in desc

