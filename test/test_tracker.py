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

def test_mark_failed_and_recently_failed(tmp_path):
    db = tmp_path / "history.db"
    tracker = UploadTracker(db)

    assert not tracker.is_recently_failed("456")

    tracker.mark_as_failed("456")
    
    assert tracker.is_recently_failed("456")

def test_recently_failed_expired(tmp_path):
    import sqlite3
    db = tmp_path / "history.db"
    tracker = UploadTracker(db)
    
    # Manually insert a record that is 25 hours old
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO failed_uploads (tiktok_id, failed_at) VALUES (?, datetime('now', '-25 hours'))",
            ("789",)
        )
        conn.commit()

    assert not tracker.is_recently_failed("789")

def test_mark_uploaded_clears_failed(tmp_path):
    db = tmp_path / "history.db"
    tracker = UploadTracker(db)
    
    tracker.mark_as_failed("999")
    assert tracker.is_recently_failed("999")
    
    tracker.mark_as_uploaded("999", "xyz")
    assert tracker.is_uploaded("999")
    assert not tracker.is_recently_failed("999")