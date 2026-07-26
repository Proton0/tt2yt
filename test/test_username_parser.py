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
    t = TikTok("www.tiktok.com/@vproton0")
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