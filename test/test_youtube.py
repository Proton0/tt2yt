import pytest
from unittest.mock import patch
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