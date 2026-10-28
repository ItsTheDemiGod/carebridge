"""Phase 8a: the history scanner on a synthetic temporary git repository with FAKE secrets and personal data. It must find them, redact them and never print the value."""
import json
import subprocess
import sys

from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import scan_repo_history as S  # noqa: E402

FAKE_GOOGLE = "AIza" + "B" * 35
FAKE_GH = "ghp_" + "c" * 36
FAKE_ENVVAL = "zzFakeSecretValue123"
FAKE_EMAIL = "someone@fakeexample.org"
FAKE_FERNET = "A" * 43 + "="
BS = chr(92)


def g(repo, *a):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True)


def make_repo(tmp_path):
    g(tmp_path, "init", "-q")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / ".env").write_text(f"GEMINI_API_KEY={FAKE_ENVVAL}\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text(f"key {FAKE_GOOGLE} and {FAKE_GH}\nmail {FAKE_EMAIL}\nURK12345 C:{BS}Users{BS}Someone{BS}Desktop\nfernet {FAKE_FERNET}\n", encoding="utf-8")
    (tmp_path / "ok.md").write_text("GEMINI_API_KEY=your_key_here\n", encoding="utf-8")
    g(tmp_path, "add", "-A")
    g(tmp_path, "commit", "-q", "-m", "one")
    g(tmp_path, "rm", "-q", "-r", "--cached", "backend")  # removed from the tree, still in history
    g(tmp_path, "commit", "-q", "-m", "two")


def test_finds_everything_redacts_and_never_prints_the_value(tmp_path, capsys):
    make_repo(tmp_path)
    out = tmp_path / "out" / "r.json"
    S.main(["--repo", str(tmp_path), "--json", str(out), "--summary", str(tmp_path / "s.md")])
    printed = capsys.readouterr().out
    rep = json.loads(out.read_text(encoding="utf-8"))
    pats = {f["pattern"] for f in rep["findings"]}
    assert {"google_api_key", "github_token", "key_assignment:GEMINI_API_KEY", "possible_fernet_key", "registration_number_URK"} <= pats
    assert any(e["pattern"] == "env_file" and not e["in_tree"] for e in rep["never_tracked"])  # in history only
    assert any(e["domain"] == "fakeexample.org" for e in rep["email_domains"]) and rep["winpaths"]
    assert not any(f["path"] == "ok.md" for f in rep["findings"])  # a placeholder value is not a secret
    everything = printed + out.read_text(encoding="utf-8") + (tmp_path / "s.md").read_text(encoding="utf-8")
    for v in (FAKE_GOOGLE, FAKE_GH, FAKE_ENVVAL, FAKE_EMAIL, FAKE_FERNET, "Someone"):
        assert v not in everything
    assert all(len(f["preview"]) < 40 for f in rep["findings"])


def test_folder_mode_scans_a_built_output(tmp_path, capsys):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "a.js").write_text(f'x="{FAKE_GOOGLE}"', encoding="utf-8")
    S.main(["--tree", str(tmp_path), "--json", str(tmp_path.parent / "t.json")])
    rep = json.loads((tmp_path.parent / "t.json").read_text(encoding="utf-8"))
    assert rep["mode"] == "folder" and any(f["pattern"] == "google_api_key" for f in rep["findings"]) and FAKE_GOOGLE not in capsys.readouterr().out
