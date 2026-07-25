from tracker import UploadTracker

def test_mark_uploaded(tmp_path):
    db = tmp_path / "history.db"

    tracker = UploadTracker(db)

    assert not tracker.is_uploaded("123")

    tracker.mark_as_uploaded("123", "abc")

    assert tracker.is_uploaded("123")