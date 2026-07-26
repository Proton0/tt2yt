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

@patch('sys.stderr', new_callable=MagicMock)
def test_load_global_secrets_invalid_json(mock_stderr):
    with patch("pathlib.Path.is_file", return_value=True), \
         patch("pathlib.Path.open", mock_open(read_data="invalid json")):
        assert main.load_global_secrets() == {}
        mock_stderr.write.assert_any_call("Warning: Failed to decode secrets/secrets.json. Using empty secrets.")



def test_save_global_secrets_success():
    secrets = {"tiktok_profile": "test_profile"}
    with patch("pathlib.Path.mkdir") as mock_mkdir, \
         patch("pathlib.Path.open", mock_open()) as mock_file:
        main.save_global_secrets(secrets)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        handle = mock_file()
        written = "".join(call.args[0] for call in handle.write.mock_calls)
        assert '"tiktok_profile": "test_profile"' in written

@patch('sys.stderr', new_callable=MagicMock)
def test_save_global_secrets_exception(mock_stderr):
    secrets = {"test": "data"}
    with patch("pathlib.Path.mkdir", side_effect=Exception("mkdir failed")):
        main.save_global_secrets(secrets)
        mock_stderr.write.assert_any_call("Error saving secrets to secrets/secrets.json: mkdir failed")



def test_load_env_secrets_no_vars_set():
    """Returns empty dict when no TT2YT_* env vars are present."""
    env = {k: v for k, v in __import__('os').environ.items()
           if not k.startswith("TT2YT_")}
    with patch.dict("os.environ", env, clear=True):
        assert main.load_env_secrets() == {}

def test_load_env_secrets_simple_vars():
    env = {
        "TT2YT_TIKTOK_PROFILE": "env_profile",
        "TT2YT_TIKTOK_CHANNEL_ID": "env_channel",
        "TT2YT_OPENROUTER_KEY": "env_key",
    }
    with patch.dict("os.environ", env, clear=True):
        result = main.load_env_secrets()
    assert result["tiktok_profile"] == "env_profile"
    assert result["tiktok_channel_id"] == "env_channel"
    assert result["openrouter_key"] == "env_key"
    assert "client_secrets" not in result

def test_load_env_secrets_client_secrets_inline_json():
    payload = {"installed": {"client_id": "from_env"}}
    env = {"TT2YT_CLIENT_SECRETS": json.dumps(payload)}
    with patch.dict("os.environ", env, clear=True):
        result = main.load_env_secrets()
    assert result["client_secrets"] == payload

@patch('sys.stderr', new_callable=MagicMock)
def test_load_env_secrets_client_secrets_invalid_json(mock_stderr):
    env = {"TT2YT_CLIENT_SECRETS": "not-valid-json"}
    with patch.dict("os.environ", env, clear=True):
        result = main.load_env_secrets()
    assert "client_secrets" not in result
    # stderr should have warned the user
    written = "".join(call.args[0] for call in mock_stderr.write.mock_calls)
    assert "TT2YT_CLIENT_SECRETS" in written
    assert "not valid JSON" in written

def test_load_env_secrets_client_secrets_file_path():
    payload = {"installed": {"client_id": "from_file"}}
    env = {"TT2YT_CLIENT_SECRETS_FILE": "/fake/path/client_secrets.json"}
    with patch.dict("os.environ", env, clear=True), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("pathlib.Path.open", mock_open(read_data=json.dumps(payload))):
        result = main.load_env_secrets()
    assert result["client_secrets"] == payload

@patch('sys.stderr', new_callable=MagicMock)
def test_load_env_secrets_client_secrets_file_not_found(mock_stderr):
    env = {"TT2YT_CLIENT_SECRETS_FILE": "/nonexistent/secrets.json"}
    with patch.dict("os.environ", env, clear=True), \
         patch("pathlib.Path.is_file", return_value=False):
        result = main.load_env_secrets()
    assert "client_secrets" not in result
    written = "".join(call.args[0] for call in mock_stderr.write.mock_calls)
    assert "does not exist" in written

@patch('sys.stderr', new_callable=MagicMock)
def test_load_env_secrets_client_secrets_file_read_error(mock_stderr):
    env = {"TT2YT_CLIENT_SECRETS_FILE": "/fake/path/client_secrets.json"}
    with patch.dict("os.environ", env, clear=True), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("pathlib.Path.open", side_effect=OSError("permission denied")):
        result = main.load_env_secrets()
    assert "client_secrets" not in result
    written = "".join(call.args[0] for call in mock_stderr.write.mock_calls)
    assert "Could not read" in written

def test_load_env_secrets_inline_json_takes_precedence_over_file():
    """TT2YT_CLIENT_SECRETS (JSON) should win over TT2YT_CLIENT_SECRETS_FILE."""
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
    assert secrets['client_secrets'] == {"client_id": "test"}
    mock_save.assert_called_once()

def test_parse_secrets_fallback_to_global():
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id=None,
        openrouter_key=None,
        client_secrets_file=None
    )
    global_secrets = {
        "tiktok_profile": "global_profile",
        "tiktok_channel_id": "global_channel",
        "openrouter_key": "global_key",
        "client_secrets": {"client_id": "global_test"}
    }
    with patch("main.load_global_secrets", return_value=global_secrets), \
         patch("main.load_env_secrets", return_value={}), \
         patch("main.save_global_secrets") as mock_save:
        secrets = main.parse_secrets(args)
    assert secrets['tiktok_profile'] == 'global_profile'
    assert secrets['tiktok_channel_id'] == 'global_channel'
    assert secrets['openrouter_key'] == 'global_key'
    assert secrets['client_secrets'] == {"client_id": "global_test"}
    mock_save.assert_not_called()

def test_parse_secrets_missing_tiktok_info():
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id=None,
        openrouter_key=None,
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
        client_secrets_file=None
    )
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value={}):
        with pytest.raises(RuntimeError, match="Missing required configuration for: client_secrets_file"):
            main.parse_secrets(args)

@patch('sys.stderr', new_callable=MagicMock)
def test_parse_secrets_invalid_client_secrets_file(mock_stderr):
    args = argparse.Namespace(
        tiktok_profile="profile",
        tiktok_channel_id=None,
        openrouter_key="key",
        client_secrets_file="dummy.json"
    )
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value={}), \
         patch("pathlib.Path.is_file", return_value=True), \
         patch("builtins.open", side_effect=Exception("read failed")):
        with pytest.raises(RuntimeError, match="Missing required configuration for: client_secrets"):
            main.parse_secrets(args)
    mock_stderr.write.assert_any_call("Error loading client secrets from dummy.json: read failed")



def test_parse_secrets_env_vars_override_global():
    """Env vars should beat the secrets file when CLI args are absent."""
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id=None,
        openrouter_key=None,
        client_secrets_file=None,
    )
    global_secrets = {
        "tiktok_channel_id": "global_channel",
        "openrouter_key": "global_key",
        "client_secrets": {"client_id": "global"},
    }
    env_secrets = {
        "tiktok_channel_id": "env_channel",
        "openrouter_key": "env_key",
        "client_secrets": {"client_id": "env"},
    }
    with patch("main.load_global_secrets", return_value=global_secrets), \
         patch("main.load_env_secrets", return_value=env_secrets), \
         patch("main.save_global_secrets"):
        secrets = main.parse_secrets(args)
    assert secrets["tiktok_channel_id"] == "env_channel"
    assert secrets["openrouter_key"] == "env_key"
    assert secrets["client_secrets"] == {"client_id": "env"}

def test_parse_secrets_cli_overrides_env_vars():
    """CLI args should beat env vars."""
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id="cli_channel",
        openrouter_key="cli_key",
        client_secrets_file="cli.json",
    )
    env_secrets = {
        "tiktok_channel_id": "env_channel",
        "openrouter_key": "env_key",
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
    assert secrets["client_secrets"] == {"client_id": "cli"}

def test_parse_secrets_env_client_secrets_used_when_no_cli_file():
    """When no CLI file is given, env client_secrets should be used."""
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id="some_channel",
        openrouter_key=None,
        client_secrets_file=None,
    )
    env_secrets = {"client_secrets": {"client_id": "from_env"}}
    with patch("main.load_global_secrets", return_value={}), \
         patch("main.load_env_secrets", return_value=env_secrets), \
         patch("main.save_global_secrets"):
        secrets = main.parse_secrets(args)
    assert secrets["client_secrets"] == {"client_id": "from_env"}

def test_parse_secrets_env_tiktok_profile_only():
    """Env-supplied profile (without channel ID) should work as a fallback."""
    args = argparse.Namespace(
        tiktok_profile=None,
        tiktok_channel_id=None,
        openrouter_key=None,
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



def test_main_execution():
    with patch("sys.argv", ["main.py", "-tc", "channel123", "-c", "dummy.json"]), \
         patch("main.parse_secrets") as mock_parse, \
         patch("main.TT2YT") as mock_tt2yt:
        mock_parse.return_value = {"tiktok_channel_id": "channel123"}
        main.main()
        mock_parse.assert_called_once()
        mock_tt2yt.assert_called_once()
        mock_tt2yt.return_value.run.assert_called_once()

@patch('sys.stderr', new_callable=MagicMock)
def test_main_runtime_error(mock_stderr):
    with patch("sys.argv", ["main.py"]), \
         patch("main.parse_secrets", side_effect=RuntimeError("Test error")):
        with pytest.raises(SystemExit) as excinfo:
            main.main()
        assert excinfo.value.code == 1
        mock_stderr.write.assert_any_call("Fatal Error: Test error")
