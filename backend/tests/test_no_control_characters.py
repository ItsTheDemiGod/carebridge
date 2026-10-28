"""Phase 8a: no tracked text file may contain ASCII control characters (other than newline, carriage return, tab) or the U+FFFD replacement character.
They appeared when Windows backslash sequences (backslash-b, -a, -f) in commands were turned into control characters."""
import re
import subprocess

from app.services.guards import REPO

BAD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f�]")
TEXT = (".md", ".py", ".ts", ".tsx", ".json", ".csv", ".txt", ".yml", ".yaml", ".css", ".html", ".mjs", ".js", ".toml", ".cfg", ".example", ".webmanifest", ".svg")


def test_no_tracked_text_file_has_control_characters():
    files = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout.split("\n")
    hits = []
    for f in files:
        if not f.endswith(TEXT) and f not in {".gitignore", "LICENSE"}:
            continue
        try:
            text = (REPO / f).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        hits += [f"{f}:{i}" for i, line in enumerate(text.split("\n"), 1) if BAD.search(line)]
    assert not hits, f"control characters in: {hits[:10]}"
