"""Chooses and copies the three synthetic documents of the usability test (Phase 7a). Dev and stress items only, never the test split; no model call.

  python scripts/prepare_usability_samples.py (with the backend venv)

U1: a dev document (clean image) whose CACHED normalised extraction has exactly one medicine at must_confirm (and 3 or more medicines).
U2: a dev document (scan image) whose cached extraction has a near-miss name that needs the formulary picker.
U3: a stress prescription with a designed major interaction (clean image).
Images are copied (re-encoded as JPEG quality 92 to keep them small) to data/usability_samples/U1.jpg..U3.jpg (synthetic, committed); the mapping to the source ids stays in the gitignored data/usability_samples/mapping.json."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))

from PIL import Image  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput  # noqa: E402
from app.services.normalisation import normalise_document  # noqa: E402

OUT = REPO / "data" / "usability_samples"
RAW = REPO / "eval" / "runs" / "dev-ollama-v1" / "raw"


def dev_ids(root: Path) -> list[str]:
    return sorted(d["id"] for d in json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))["documents"] if d["split"] == "dev")


def normalised(cond: str, doc: str):
    f = RAW / f"{cond}_{doc}.json"
    return normalise_document(ExtractionOutput.model_validate_json(f.read_text(encoding="utf-8"))) if f.exists() else None


def pick_u1(ids):
    for d in ids:
        nd = normalised("clean", d)
        if nd and len(nd.medications) >= 3 and sum(m.review_level == "must_confirm" for m in nd.medications) == 1:
            return d
    raise SystemExit("no dev document fits U1")


def pick_u2(ids, exclude):
    for d in ids:
        nd = normalised("scan", d)
        if d not in exclude and nd and len(nd.medications) >= 3 and any({"near_miss_name", "unresolved_name"} & set(m.flags) for m in nd.medications):
            return d
    raise SystemExit("no dev document fits U2")


def main() -> None:
    ids = dev_ids(REPO)
    u1 = pick_u1(ids)
    u2 = pick_u2(ids, {u1})
    st = json.loads((REPO / "data/stress/manifest.json").read_text(encoding="utf-8"))["documents"]
    u3 = next(d["id"] for d in st if d["category"] == "major_pair")
    OUT.mkdir(parents=True, exist_ok=True)
    plan = {"U1": ("dev", u1, REPO / "data/rendered/clean" / f"{u1}.png"), "U2": ("dev", u2, REPO / "data/rendered/scan" / f"{u2}.png"), "U3": ("stress", u3, REPO / "data/stress/rendered/clean" / f"{u3}.png")}
    for k, (_s, _i, src) in plan.items():
        Image.open(src).convert("L").save(OUT / f"{k}.jpg", "JPEG", quality=92)
    (OUT / "mapping.json").write_text(json.dumps({k: {"source": s, "id": i, "image": str(p.relative_to(REPO))} for k, (s, i, p) in plan.items()}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("prepared U1, U2 (dev) and U3 (stress); mapping kept private")


if __name__ == "__main__":
    main()
