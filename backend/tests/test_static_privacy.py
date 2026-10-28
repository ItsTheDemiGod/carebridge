"""Phase 8a: the static consent notice of the hosted-sample build equals what the real API serves (same templates), in all three languages."""
import json
import sys

from app.services import consent
from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import build_static_privacy as B  # noqa: E402


def test_static_notice_is_up_to_date_and_equals_the_api_notice():
    assert B.OUT.read_text(encoding="utf-8") == B.build(), "run: python scripts/build_static_privacy.py"
    data = json.loads(B.OUT.read_text(encoding="utf-8"))
    for lang in ("en", "ta", "hi"):
        assert data[lang] == json.loads(json.dumps(consent.notice(lang)))
        assert data[lang]["items"] and data[lang]["purposes"]
