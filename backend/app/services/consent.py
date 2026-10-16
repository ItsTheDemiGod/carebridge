"""The consent notice: assembled from templates, versioned and hashed. Bump NOTICE_VERSION whenever the text changes
(a test pins the English hash to the version, so a text change without a bump fails)."""
import hashlib
import json

from app.services import templates as T

NOTICE_VERSION = "1"
ITEMS = ("what", "where", "stored", "how_long", "delete", "no_sharing", "prototype", "contact")
PURPOSES = {"process_photo": True, "store_results_for_session": True, "keep_photo_for_session": False}  # id -> required
REQUIRED = {p for p, req in PURPOSES.items() if req}


def notice(lang: str) -> dict:
    items = [{"id": i, "text": T.render(f"consent.item.{i}", lang)} for i in ITEMS]
    purposes = [{"id": p, "label": T.render(f"consent.purpose.{p}", lang), "required": req, "default": req} for p, req in PURPOSES.items()]
    title = T.render("consent.title", lang)
    canonical = json.dumps({"version": NOTICE_VERSION, "lang": lang, "title": title, "items": items, "purposes": purposes}, ensure_ascii=False, sort_keys=True)
    return {"version": NOTICE_VERSION, "language": lang, "sha256": hashlib.sha256(canonical.encode()).hexdigest(), "title": title, "items": items, "purposes": purposes,
            "review_status": {"en": "not_required"}.get(lang, "draft_unreviewed")}


def valid_purposes(granted: list[str]) -> bool:
    return set(granted) <= set(PURPOSES) and REQUIRED <= set(granted)
