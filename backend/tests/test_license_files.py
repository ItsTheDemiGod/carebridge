"""Phase 8a: the project licence is MIT (owner decision); the demo fixtures carry the DDInter exclusion note."""
from app.services.guards import REPO


def test_license_is_mit_and_names_no_email():
    t = (REPO / "LICENSE").read_text(encoding="utf-8")
    assert t.startswith("MIT License") and "Copyright (c) 2026 Demian" in t and "@" not in t


def test_demo_fixtures_note_excludes_ddinter_from_mit():
    t = (REPO / "frontend" / "src" / "demo" / "fixtures" / "README.md").read_text(encoding="utf-8")
    assert "CC BY-NC-SA 4.0" in t and "not** covered by the project's MIT licence" in t and "not medical advice" in t
