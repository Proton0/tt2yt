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


from tiktok import TikTok
import pytest
import random
import string

def test_profile_url():
    t = TikTok("https://www.tiktok.com/@vproton0")
    assert t.tiktok_profile == "vproton0"

def test_profile_url_no_https():
    t = TikTok("www.tiktok.com/@vproton0")
    assert t.tiktok_profile == "vproton0"

def test_profile_url_no_https_www():
    t = TikTok("tiktok.com/@vproton0")
    assert t.tiktok_profile == "vproton0"

def test_profile_url_no_www():
    t = TikTok("tiktok.com/@vproton0")
    assert t.tiktok_profile == "vproton0"

def test_profile_url_with_junk():
    t = TikTok("https://www.tiktok.com/@vproton0?junk_bs=1&very_very_junk=67")
    assert t.tiktok_profile == "vproton0"

def test_profile_url_worse_case():
    t = TikTok("tiktok.com/@vproton0/?junk=1&very_junk=67")
    assert t.tiktok_profile == "vproton0"

def test_profile_at():
    t = TikTok("@vproton0")
    assert t.tiktok_profile == "vproton0"

def test_profile_plain():
    t = TikTok("vproton0")
    assert t.tiktok_profile == "vproton0"

def test_tiktok_init_missing_args():
    with pytest.raises(ValueError, match="Both tiktok_profile and tiktok_channel_id are None"):
        TikTok(tiktok_profile=None, tiktok_channel_id=None)

def test_tiktok_init_empty_args():
    with pytest.raises(ValueError, match="Both tiktok_profile and tiktok_channel_id are empty"):
        TikTok(tiktok_profile="", tiktok_channel_id="")

def test_profile_channel_id():
    t = TikTok(None, "MS4wLjABAAAA_3nK1eKl6nn2JV3s2PJ95tUKmnORf_SXoGMBWyYRK8atwrEfuwbPOxGfSPD9fMGf")
    assert t.tiktok_channel_id == "MS4wLjABAAAA_3nK1eKl6nn2JV3s2PJ95tUKmnORf_SXoGMBWyYRK8atwrEfuwbPOxGfSPD9fMGf"


def generate_random_usernames(n=5):
    usernames = []
    for i in range(n):
        length = random.randint(2, 24)

        if i == 0:
            chars = string.ascii_letters  # Only letters
        elif i == 1:
            chars = string.digits  # Only numbers
        else:
            chars = string.ascii_letters + string.digits + "_."  # Mixed characters

        username = "".join(random.choices(chars, k=length))

        if username.endswith('.'):
            username = username[:-1] + random.choice(string.ascii_letters)

        usernames.append(username)
    return usernames

def generate_random_channel_ids(n=5):
    chars = string.ascii_letters + string.digits + "_-"
    return ["".join(random.choices(chars, k=72)) for _ in range(n)]


@pytest.mark.parametrize("username", generate_random_usernames(5))
def test_profile_url_random(username):
    t = TikTok(f"https://www.tiktok.com/@{username}")
    assert t.tiktok_profile == username

@pytest.mark.parametrize("username", generate_random_usernames(5))
def test_profile_url_no_https_random(username):
    t = TikTok(f"www.tiktok.com/@{username}")
    assert t.tiktok_profile == username

@pytest.mark.parametrize("username", generate_random_usernames(5))
def test_profile_url_no_https_www_random(username):
    t = TikTok(f"tiktok.com/@{username}")
    assert t.tiktok_profile == username

@pytest.mark.parametrize("username", generate_random_usernames(5))
def test_profile_url_no_www_random(username):
    t = TikTok(f"https://tiktok.com/@{username}")
    assert t.tiktok_profile == username

@pytest.mark.parametrize("username", generate_random_usernames(5))
def test_profile_url_with_junk_random(username):
    t = TikTok(f"https://www.tiktok.com/@{username}?junk_bs=1&very_very_junk=67")
    assert t.tiktok_profile == username

@pytest.mark.parametrize("username", generate_random_usernames(5))
def test_profile_url_worse_case_random(username):
    t = TikTok(f"tiktok.com/@{username}/?junk=1&very_junk=67")
    assert t.tiktok_profile == username

@pytest.mark.parametrize("username", generate_random_usernames(5))
def test_profile_at_random(username):
    t = TikTok(f"@{username}")
    assert t.tiktok_profile == username

@pytest.mark.parametrize("username", generate_random_usernames(5))
def test_profile_plain_random(username):
    t = TikTok(username)
    assert t.tiktok_profile == username


@pytest.mark.parametrize("channel_id", generate_random_channel_ids(5))
def test_profile_channel_id_random(channel_id):
    t = TikTok(None, channel_id)
    assert t.tiktok_channel_id == channel_id