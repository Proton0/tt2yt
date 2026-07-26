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


from tracker import UploadTracker

def test_mark_uploaded(tmp_path):
    db = tmp_path / "history.db"

    tracker = UploadTracker(db)

    assert not tracker.is_uploaded("123")

    tracker.mark_as_uploaded("123", "abc")

    assert tracker.is_uploaded("123")