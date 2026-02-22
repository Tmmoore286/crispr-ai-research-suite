"""Tests for the collaboration module."""

from crisprairs.rpw.collaboration import Collaboration
from crisprairs.rpw.sessions import SessionManager


def _patch_dirs(tmp_path, monkeypatch):
    """Patch all SESSIONS_DIR and AUDIT_DIR references for collaboration tests."""
    import crisprairs.rpw.sessions as smod
    import crisprairs.rpw.audit as amod
    import crisprairs.rpw.collaboration as cmod

    monkeypatch.setattr(smod, "SESSIONS_DIR", tmp_path)
    monkeypatch.setattr(cmod, "SESSIONS_DIR", tmp_path)
    monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path / "audit")
    (tmp_path / "audit").mkdir(exist_ok=True)


class TestSharing:
    def test_share_session(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        SessionManager.save("s1", chat_history=[])
        token = Collaboration.share_session("s1", owner="Tim")

        assert token is not None
        assert len(token) == 12

    def test_share_nonexistent_returns_none(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        assert Collaboration.share_session("nope") is None

    def test_lookup_by_token(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        SessionManager.save("s2", chat_history=[])
        token = Collaboration.share_session("s2")

        found = Collaboration.lookup_by_token(token)
        assert found == "s2"

    def test_lookup_unknown_token(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        assert Collaboration.lookup_by_token("unknown") is None


class TestAnnotations:
    def test_add_and_list(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        SessionManager.save("s3", chat_history=[("Hello", "Hi")])
        result = Collaboration.add_annotation("s3", 0, "Good response", "Dr. Smith")
        assert result is True

        annotations = Collaboration.list_annotations("s3")
        assert len(annotations) == 1
        assert annotations[0]["author"] == "Dr. Smith"

    def test_get_annotations_for_step(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        SessionManager.save("s4", chat_history=[])
        Collaboration.add_annotation("s4", 0, "Comment A", "User1")
        Collaboration.add_annotation("s4", 1, "Comment B", "User2")

        step0 = Collaboration.get_annotations_for_step("s4", 0)
        assert len(step0) == 1
        assert step0[0]["comment"] == "Comment A"

    def test_annotation_nonexistent_session(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        assert Collaboration.add_annotation("nope", 0, "x", "y") is False

    def test_format_annotations_markdown(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        SessionManager.save("s5", chat_history=[])
        Collaboration.add_annotation("s5", 0, "Nice work", "PI")
        md = Collaboration.format_annotations_markdown("s5")
        assert "Annotations" in md
        assert "Nice work" in md


class TestPIReview:
    def test_request_and_complete(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        SessionManager.save("s6", chat_history=[])

        assert Collaboration.request_pi_review("s6", requester="Student") is True
        status = Collaboration.get_pi_review_status("s6")
        assert status["status"] == "pending"

        assert Collaboration.complete_pi_review("s6", "Dr. PI", "approved", "Looks good") is True
        status = Collaboration.get_pi_review_status("s6")
        assert status["status"] == "completed"
        assert status["decision"] == "approved"

    def test_review_nonexistent(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        assert Collaboration.request_pi_review("nope") is False
        assert Collaboration.complete_pi_review("nope", "PI", "approved") is False

    def test_complete_without_request(self, tmp_path, monkeypatch):
        _patch_dirs(tmp_path, monkeypatch)

        SessionManager.save("s7", chat_history=[])
        assert Collaboration.complete_pi_review("s7", "PI", "approved") is False
