import pytest
import json
import argparse
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys

import main


def test_load_global_secrets_no_file():
    with patch("pathlib.Path.is_file", return_value=False):
        assert main.load_global_secrets() == {}

def test_load_global_secrets_valid_file():
    mock_data = '{"tiktok_profile": "test_profile"}'
    with patch("pathlib.Path.is_file", return_value=True), \
         patch("pathlib.Path.open", mock_open(read_data=mock_data)):
        assert main.load_global_secrets() == {"tiktok_profile": "test_profile"}

@patch('main.logger')
def test_load_global_secrets_invalid_json(mock_logger):
    with patch("pathlib.Path.is_file", return_value=True), \
         patch("pathlib.Path.open", mock_open(read_data="invalid json")):
        assert main.load_global_secrets() == {}
        mock_logger.warning.assert_called_once_with("Failed to decode secrets/secrets.json. Using empty secrets.")


def test_save_global_secrets_success():
    secrets = {"tiktok_profile": "test_profile"}
    with patch("pathlib.Path.mkdir") as mock_mkdir, \
         patch("pathlib.Path.open", mock_open()) as mock_file:
        main.save_global_secrets(secrets)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        handle = mock_file()
        written = "".join(call.args[0] for call in handle.write.mock_calls)
        assert '"tiktok_profile": "test_profile"' in written

@patch('main.logger')
def test_save_global_secrets_exception(mock_logger):
    secrets = {"test": "data"}
    with patch("pathlib.Path.mkdir", side_effect=Exception("mkdir failed")):
        main.save_global_secrets(secrets)
        mock_logger.error.assert_called_once_with("Error saving secrets to secrets/secrets.json: mkdir failed")


def test_load_env_secrets_no_vars_set():
    env = {k: v for k, v in __import__('os').environ.items() if not k.startswith("TT2YT_")}
    with patch.dict("os.environ", env, clear=True):
        assert main.load_env_secrets() == {}

def test_load_env_secrets_simple_vars():
    env = {
        "TT2YT_TIKTOK_PROFILE": "env_profile",
        "TT2YT_TIKTOK_CHANNEL_ID": "env_channel",
        "TT2YT_OPENROUTER_KEY": "env_key",
        "TT2YT_DISCORD_WEBHOOK_URL": "env_webhook",
    }
    with patch.dict("os.environ", env, clear=True):
        result = main.load_env_secrets()
    assert result["tiktok_profile"] == "env_profile"
    assert result["tiktok_channel_id"] == "env_channel"
    assert result["openrouter_key"] == "env_key"
    assert result["discord_webhook_url"] == "env_webhook"
    assert "client_secrets" not in result

def test_load_env_secrets_client_secrets_inline_json():
    payload = {"installed": {"client_id": "from_env"}}
    env = {"TT2YT_CLIENT_SECRETS": json.dumps(payload)}
    with patch.dict("os.environ", env, clear=True):
        result = main.load_env_secrets()
    assert result["client_secrets"] == payload

@patch('main.logger')
def test_load_env_secrets_client_secrets_invalid_json(mock_logger):
    env = {"TT2YT_CLIENT_SECRETS": "not-valid-json"}
    with patch.dict("os.environ", env, clear=True):
        result = main.load_env_secrets()
    assert "client_secrets" not in result
    mock_logger.warning.assert_called_once()
    assert "not valid JSON" in mock_logger.warning.call_args[0][0]

def test_load_env_secrets_client_secrets_file_path():
    payload = {"installed": {"client_id": "from_file"}}
    env = {"TT2YT_CLIENT_SECRETS_FILE": "/fake/path/client_secrets.json"}
    with patch.dict("os.environ", env, clear=True), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("pathlib.Path.open", mock_open(read_data=json.dumps(payload))):
        result = main.load_env_secrets()
    assert result["client_secrets"] == payload

@patch('main.logger')
def test_load_env_secrets_client_secrets_file_not_found(mock_logger):
    env = {"TT2YT_CLIENT_SECRETS_FILE": "/nonexistent/secrets.json"}
    with patch.dict("os.environ", env, clear=True), \
         patch("pathlib.Path.is_file", return_value=False):
        result = main.load_env_secrets()
    assert "client_secrets" not in result

@patch('main.logger')
def test_load_env_secrets_client_secrets_file_read_error(mock_logger):
    env = {"TT2YT_CLIENT_SECRETS_FILE": "/fake/path/client_secrets.json"}
    with patch.dict("os.environ", env, clear=True), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("pathlib.Path.open", side_effect=OSError("permission denied")):
        result = main.load_env_secrets()
    assert "client_secrets" not in result

def test_load_env_secrets_inline_json_takes_precedence_over_file():
    inline = {"installed": {"client_id": "inline"}}
    file_payload = {"installed": {"client_id": "file"}}
    env = {
        "TT2YT_CLIENT_SECRETS": json.dumps(inline),
        "TT2YT_CLIENT_SECRETS_FILE": "/fake/path/client_secrets.json",
    }
    with patch.dict("os.environ", env, clear=True), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("pathlib.Path.open", mock_open(read_data=json.dumps(file_payload))):
        result = main.load_env_secrets()
    assert result["client_secrets"] == inline


def test_parse_secrets_all_args():
    args = argparse.Namespace(
        tiktok_profile="cli_profile",
        tiktok_channel_id="cli_channel",
        openrouter_key="cli_key",
        discord_webhook_url="cli_webhook",
        client_secrets_file="dummy.json"
    )
    mock_secrets_data = '{"client_id": "test"}'
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value={}), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_secrets_data)), \
         patch("main.save_global_secrets") as mock_save:
        secrets = main.parse_secrets(args)
    assert secrets['tiktok_profile'] == 'cli_profile'
    assert secrets['tiktok_channel_id'] == 'cli_channel'
    assert secrets['openrouter_key'] == 'cli_key'
    assert secrets['discord_webhook_url'] == 'cli_webhook'
    assert secrets['client_secrets'] == {"client_id": "test"}
    mock_save.assert_called_once()

def test_parse_secrets_fallback_to_global():
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id=None,
        openrouter_key=None,
        discord_webhook_url=None,
        client_secrets_file=None
    )
    global_secrets = {
        "tiktok_profile": "global_profile",
        "tiktok_channel_id": "global_channel",
        "openrouter_key": "global_key",
        "discord_webhook_url": "global_webhook",
        "client_secrets": {"client_id": "global_test"}
    }
    with patch("main.load_global_secrets", return_value=global_secrets), \
         patch("main.load_env_secrets", return_value={}), \
         patch("main.save_global_secrets") as mock_save:
        secrets = main.parse_secrets(args)
    assert secrets['tiktok_profile'] == 'global_profile'
    assert secrets['tiktok_channel_id'] == 'global_channel'
    assert secrets['openrouter_key'] == 'global_key'
    assert secrets['discord_webhook_url'] == 'global_webhook'
    assert secrets['client_secrets'] == {"client_id": "global_test"}
    mock_save.assert_not_called()

def test_parse_secrets_missing_tiktok_info():
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id=None,
        openrouter_key=None,
        discord_webhook_url=None,
        client_secrets_file="dummy.json"
    )
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value={}), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("builtins.open", mock_open(read_data='{}')):
        with pytest.raises(RuntimeError, match="Missing required configuration for: tiktok_channel_id, tiktok_profile"):
            main.parse_secrets(args)

def test_parse_secrets_missing_client_secrets():
    args = argparse.Namespace(
        tiktok_profile="profile",
        tiktok_channel_id=None,
        openrouter_key="key",
        discord_webhook_url=None,
        client_secrets_file=None
    )
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value={}):
        with pytest.raises(RuntimeError, match="Missing required configuration for: client_secrets_file"):
            main.parse_secrets(args)

@patch('main.logger')
def test_parse_secrets_invalid_client_secrets_file(mock_logger):
    args = argparse.Namespace(
        tiktok_profile="profile",
        tiktok_channel_id=None,
        openrouter_key="key",
        discord_webhook_url=None,
        client_secrets_file="dummy.json"
    )
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value={}), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("builtins.open", side_effect=Exception("read failed")):
        with pytest.raises(RuntimeError, match="Missing required configuration for: client_secrets"):
            main.parse_secrets(args)

def test_parse_secrets_env_vars_override_global():
    args = argparse.Namespace(
        tiktok_profile="test",
        tiktok_channel_id=None,
        openrouter_key=None,
        discord_webhook_url=None,
        client_secrets_file=None,
    )
    global_secrets = {
        "tiktok_channel_id": "global_channel",
        "openrouter_key": "global_key",
        "discord_webhook_url": "global_webhook",
        "client_secrets": {"client_id": "global"},
    }
    env_secrets = {
        "tiktok_channel_id": "env_channel",
        "openrouter_key": "env_key",
        "discord_webhook_url": "env_webhook",
        "client_secrets": {"client_id": "env"},
    }
    with patch("main.load_global_secrets", return_value=global_secrets), \
         patch("main.load_env_secrets", return_value=env_secrets), \
         patch("main.save_global_secrets"):
        secrets = main.parse_secrets(args)
    assert secrets["tiktok_channel_id"] == "env_channel"
    assert secrets["openrouter_key"] == "env_key"
    assert secrets["discord_webhook_url"] == "env_webhook"
    assert secrets["client_secrets"] == {"client_id": "env"}

def test_parse_secrets_cli_overrides_env_vars():
    args = argparse.Namespace(
        tiktok_profile="test",
        tiktok_channel_id="cli_channel",
        openrouter_key="cli_key",
        discord_webhook_url="cli_webhook",
        client_secrets_file="cli.json",
    )
    env_secrets = {
        "tiktok_channel_id": "env_channel",
        "openrouter_key": "env_key",
        "discord_webhook_url": "env_webhook",
        "client_secrets": {"client_id": "env"},
    }
    mock_data = '{"client_id": "cli"}'
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value=env_secrets), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_data)), \
         patch("main.save_global_secrets"):
        secrets = main.parse_secrets(args)
    assert secrets["tiktok_channel_id"] == "cli_channel"
    assert secrets["openrouter_key"] == "cli_key"
    assert secrets["discord_webhook_url"] == "cli_webhook"
    assert secrets["client_secrets"] == {"client_id": "cli"}

def test_parse_secrets_env_client_secrets_used_when_no_cli_file():
    args = argparse.Namespace(
        tiktok_profile="test",
        tiktok_channel_id="some_channel",
        openrouter_key=None,
        discord_webhook_url=None,
        client_secrets_file=None,
    )
    env_secrets = {"client_secrets": {"client_id": "from_env"}}
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value=env_secrets), \
         patch("main.save_global_secrets"):
        secrets = main.parse_secrets(args)
    assert secrets["client_secrets"] == {"client_id": "from_env"}

def test_parse_secrets_env_tiktok_profile_only():
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id=None,
        openrouter_key=None,
        discord_webhook_url=None,
        client_secrets_file=None,
    )
    env_secrets = {
        "tiktok_profile": "env_profile",
        "client_secrets": {"client_id": "env"},
    }
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value=env_secrets), \
         patch("main.save_global_secrets"):
        secrets = main.parse_secrets(args)
    assert secrets["tiktok_profile"] == "env_profile"
    assert "tiktok_channel_id" not in secrets

def test_parse_secrets_getattr_fallback():
    args = argparse.Namespace()
    global_secrets = {
        "tiktok_profile": "global_profile",
        "client_secrets": {"client_id": "global"}
    }
    with patch("main.load_global_secrets", return_value=global_secrets), \
         patch("main.load_env_secrets", return_value={}), \
         patch("main.save_global_secrets"):
        secrets = main.parse_secrets(args)
    assert secrets["tiktok_profile"] == "global_profile"
    assert secrets["discord_webhook_url"] is None

def test_parse_secrets_invalid_json_client_secrets():
    args = argparse.Namespace(
        tiktok_profile="cli_profile",
        tiktok_channel_id=None,
        openrouter_key=None,
        discord_webhook_url=None,
        client_secrets_file="invalid.json"
    )
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value={}), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("builtins.open", mock_open(read_data="not json")):
        with pytest.raises(RuntimeError, match="Missing required configuration for: client_secrets"):
            main.parse_secrets(args)

def test_parse_secrets_saves_changes():
    args = argparse.Namespace(
        tiktok_profile="new_profile",
        tiktok_channel_id=None,
        openrouter_key=None,
        discord_webhook_url=None,
        client_secrets_file=None
    )
    global_secrets = {
        "tiktok_profile": "old_profile",
        "client_secrets": {"client_id": "global"}
    }
    with patch("main.load_global_secrets", return_value=global_secrets), \
         patch("main.load_env_secrets", return_value={}), \
         patch("main.save_global_secrets") as mock_save:
        secrets = main.parse_secrets(args)
    assert secrets["tiktok_profile"] == "new_profile"
    mock_save.assert_called_once()
    
