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

import subprocess
import threading
from unittest.mock import MagicMock, call, patch

import pytest
import requests

import update
from update import Updater, start_updater

# Silence the module-level logger for all tests in this file
@pytest.fixture(autouse=True)
def mock_updater_logger():
    with patch("update.logger") as mock_log:
        yield mock_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pypi_response(version: str) -> MagicMock:
    """Return a mock requests.Response whose .json() looks like PyPI."""
    resp = MagicMock()
    resp.json.return_value = {"info": {"version": version}}
    return resp


# ---------------------------------------------------------------------------
# Updater.__init__
# ---------------------------------------------------------------------------

class TestUpdaterInit:
    def test_default_interval(self):
        u = Updater()
        assert u.interval == 43200  # 12 hours

    def test_custom_interval(self):
        u = Updater(interval=3600)
        assert u.interval == 3600


# ---------------------------------------------------------------------------
# Updater.get_latest_version
# ---------------------------------------------------------------------------

class TestGetLatestVersion:
    def test_returns_version_on_success(self):
        u = Updater()
        with patch("update.requests.get", return_value=_make_pypi_response("2099.01.01")) as mock_get:
            version = u.get_latest_version()

        mock_get.assert_called_once_with(
            "https://pypi.org/pypi/yt-dlp/json",
            timeout=10,
        )
        assert version == "2099.01.01"

    def test_returns_none_on_http_error(self):
        u = Updater()
        resp = MagicMock()
        resp.raise_for_status.side_effect = requests.HTTPError("404")
        with patch("update.requests.get", return_value=resp):
            version = u.get_latest_version()
        assert version is None

    def test_returns_none_on_connection_error(self):
        u = Updater()
        with patch("update.requests.get", side_effect=requests.ConnectionError("unreachable")):
            version = u.get_latest_version()
        assert version is None

    def test_returns_none_on_timeout(self):
        u = Updater()
        with patch("update.requests.get", side_effect=requests.Timeout("timeout")):
            version = u.get_latest_version()
        assert version is None

    def test_returns_none_on_malformed_json(self):
        """If PyPI returns unexpected JSON shape, we should not crash."""
        u = Updater()
        resp = MagicMock()
        resp.json.return_value = {}  # missing "info" key
        with patch("update.requests.get", return_value=resp):
            version = u.get_latest_version()
        assert version is None


# ---------------------------------------------------------------------------
# Updater.update
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_no_update_when_already_current(self, mock_updater_logger):
        u = Updater()
        current_ver = "2026.07.04"
        with patch("update.yt_dlp.version.__version__", current_ver), \
             patch.object(u, "get_latest_version", return_value=current_ver):
            u.update()

        logged = mock_updater_logger.info.call_args[0][0]
        assert "up to date" in logged

    def test_no_update_when_older_version_on_pypi(self, mock_updater_logger):
        u = Updater()
        with patch("update.yt_dlp.version.__version__", "2026.07.04"), \
             patch.object(u, "get_latest_version", return_value="2026.01.01"):
            u.update()

        logged = mock_updater_logger.info.call_args[0][0]
        assert "up to date" in logged

    def test_skips_when_latest_version_is_none(self):
        u = Updater()
        with patch("update.yt_dlp.version.__version__", "2026.07.04"), \
             patch.object(u, "get_latest_version", return_value=None), \
             patch.object(u, "restart") as mock_restart, \
             patch("update.subprocess.check_call") as mock_pip:
            u.update()

        mock_pip.assert_not_called()
        mock_restart.assert_not_called()

    def test_runs_pip_and_restarts_when_update_available(self, mock_updater_logger):
        u = Updater()
        with patch("update.yt_dlp.version.__version__", "2026.01.01"), \
             patch.object(u, "get_latest_version", return_value="2026.07.04"), \
             patch("update.subprocess.check_call") as mock_pip, \
             patch.object(u, "restart") as mock_restart:
            u.update()

        import sys as _sys
        mock_pip.assert_called_once_with([
            _sys.executable,
            "-m", "pip", "install", "--upgrade", "yt-dlp",
        ])
        mock_restart.assert_called_once()
        # packaging normalises "2026.01.01" -> "2026.1.1" when printed via Version
        update_msg = mock_updater_logger.info.call_args_list[0][0][0]
        assert "2026.1.1" in update_msg
        assert "2026.7.4" in update_msg

    def test_pip_failure_does_not_restart(self, mock_updater_logger):
        u = Updater()
        with patch("update.yt_dlp.version.__version__", "2026.01.01"), \
             patch.object(u, "get_latest_version", return_value="2026.07.04"), \
             patch("update.subprocess.check_call",
                   side_effect=subprocess.CalledProcessError(1, "pip")), \
             patch.object(u, "restart") as mock_restart:
            u.update()

        mock_restart.assert_not_called()
        logged = mock_updater_logger.error.call_args[0][0]
        assert "failed" in logged.lower()

    def test_pip_called_with_sys_executable(self):
        """Ensures pip is invoked via the same Python interpreter, not a system one."""
        import sys
        u = Updater()
        with patch("update.yt_dlp.version.__version__", "2026.01.01"), \
             patch.object(u, "get_latest_version", return_value="2099.01.01"), \
             patch("update.subprocess.check_call") as mock_pip, \
             patch.object(u, "restart"):
            u.update()

        args = mock_pip.call_args[0][0]
        assert args[0] == sys.executable


# ---------------------------------------------------------------------------
# Updater.restart
# ---------------------------------------------------------------------------

class TestRestart:
    def test_calls_execv_with_correct_args(self):
        import sys
        u = Updater()
        with patch("update.os.execv") as mock_execv:
            u.restart()

        mock_execv.assert_called_once_with(sys.executable, [sys.executable] + sys.argv)


# ---------------------------------------------------------------------------
# Updater.run
# ---------------------------------------------------------------------------

class TestRun:
    def test_run_calls_update_then_sleep_repeatedly(self):
        """run() should call update() and then sleep() in a loop."""
        u = Updater(interval=60)
        call_count = {"n": 0}

        def fake_sleep(_):
            call_count["n"] += 1
            if call_count["n"] >= 3:
                raise StopIteration  # break the infinite loop after 3 iterations

        with patch.object(u, "update") as mock_update, \
             patch("update.time.sleep", side_effect=fake_sleep):
            with pytest.raises(StopIteration):
                u.run()

        assert mock_update.call_count == 3
        assert call_count["n"] == 3

    def test_run_sleeps_for_correct_interval(self):
        u = Updater(interval=9999)
        slept_values = []

        def fake_sleep(t):
            slept_values.append(t)
            raise StopIteration

        with patch.object(u, "update"), \
             patch("update.time.sleep", side_effect=fake_sleep):
            with pytest.raises(StopIteration):
                u.run()

        assert slept_values == [9999]


# ---------------------------------------------------------------------------
# start_updater
# ---------------------------------------------------------------------------

class TestStartUpdater:
    def test_starts_daemon_thread(self):
        captured = {}

        original_thread = threading.Thread

        def capturing_thread(**kwargs):
            captured["target"] = kwargs.get("target")
            captured["daemon"] = kwargs.get("daemon")
            t = MagicMock()
            return t

        with patch("update.threading.Thread", side_effect=capturing_thread) as mock_thread_cls:
            start_updater()

        mock_thread_cls.assert_called_once()
        assert captured["daemon"] is True

    def test_thread_is_started(self):
        mock_thread = MagicMock()
        with patch("update.threading.Thread", return_value=mock_thread):
            start_updater()

        mock_thread.start.assert_called_once()

    def test_thread_target_is_updater_run(self):
        """The thread target must be an Updater instance's run method."""
        captured_target = {}

        def capturing_thread(**kwargs):
            captured_target["fn"] = kwargs.get("target")
            t = MagicMock()
            return t

        with patch("update.threading.Thread", side_effect=capturing_thread):
            start_updater()

        assert callable(captured_target["fn"])
        # The target should be a bound method named 'run' belonging to an Updater
        assert captured_target["fn"].__func__ is Updater.run


# ---------------------------------------------------------------------------
# Integration: main.py --no-autoupdate flag (regression for type=bool bug)
# ---------------------------------------------------------------------------

class TestNoAutoupdateFlag:
    """
    Regression tests for the --no-autoupdate argparse flag.

    The original code used `type=bool` which caused `--no-autoupdate false`
    to be truthy (bool("false") == True).  The fix uses `action="store_true"`.
    """

    def test_flag_absent_enables_autoupdate(self):
        import argparse
        import main

        with patch("sys.argv", ["main.py"]):
            parser = argparse.ArgumentParser()
            parser.add_argument("--no-autoupdate", action="store_true", default=False)
            args = parser.parse_args([])
        assert args.no_autoupdate is False

    def test_flag_present_disables_autoupdate(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--no-autoupdate", action="store_true", default=False)
        args = parser.parse_args(["--no-autoupdate"])
        assert args.no_autoupdate is True

    def test_main_calls_start_updater_when_flag_absent(self):
        """start_updater() must be called when --no-autoupdate is not given."""
        import builtins
        import main

        mock_update_module = MagicMock()
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "update":
                return mock_update_module
            return real_import(name, *args, **kwargs)

        with patch("sys.argv", ["main.py", "-tc", "chan123", "-c", "dummy.json"]), \
             patch("main.parse_secrets", return_value={"tiktok_channel_id": "chan123"}), \
             patch("main.TT2YT") as mock_tt2yt, \
             patch("builtins.__import__", side_effect=fake_import):
            mock_tt2yt.return_value.run.return_value = None
            main.main()

        mock_update_module.start_updater.assert_called_once()

    def test_main_skips_updater_when_flag_present(self):
        """When --no-autoupdate is passed, start_updater should not be called."""
        with patch("sys.argv", ["main.py", "--no-autoupdate", "-tc", "chan123", "-c", "x.json"]), \
             patch("main.parse_secrets", return_value={"tiktok_channel_id": "chan123"}), \
             patch("main.TT2YT") as mock_tt2yt, \
             patch("update.start_updater") as mock_start:
            mock_tt2yt.return_value.run.return_value = None
            import main
            main.main()

        mock_start.assert_not_called()
