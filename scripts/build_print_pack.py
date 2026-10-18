"""Print pack for the real-photo test (Phase 7a).   backend\\.venv\\Scripts\\python scripts\\build_print_pack.py

Writes docs/real_photo_test/print_pack.pdf: five A4 pages (plain black text on white, one document per page, footer "RPn" and the fictional-document line) holding the exact
text of 3 DEV documents (different case templates, at least one with 5 or more medicines) and 2 stress-set prescriptions. The held-out test split is never used
(dev ids only, asserted). The RPn -> document mapping goes to the gitignored data/real_photos/mapping.json; the committed docs/real_photo_test/README.md maps RP ids to
document CATEGORIES only. Deterministic. Pillow only."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
DPI = 150
PAGE = (int(8.27 * DPI), int(11.69 * DPI))  # A4
MARGIN = int(0.8 * DPI)
FONTS = ["C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/consola.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
FOOTER = "Sample document for software testing only. All details are fictional."
STRESS_PICKS = ["major_pair", "garbled_name"]


def font(px: int):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, px)
    return ImageFont.load_default(size=px)


def wrap(text: str, f, width_px: int) -> list[str]:
    out = []
    for line in text.split("\n"):
        while f.getlength(line) > width_px:
            cut = line.rfind(" ", 0, max(1, int(len(line) * width_px / f.getlength(line))))
            cut = cut if cut > 0 else int(len(line) * width_px / f.getlength(line))
            out.append(line[:cut])
            line = "    " + line[cut:].lstrip()
        out.append(line)
    return out


def page_for(text: str, sample_id: str) -> Image.Image:
    for px in (30, 28, 26, 24, 22, 20):  # 14 pt down to ~9.6 pt at 150 dpi: the largest size that fits one page
        f = font(px)
        lines = wrap(text.rstrip("\n"), f, PAGE[0] - 2 * MARGIN)
        lh = int(px * 1.35)
        if len(lines) * lh <= PAGE[1] - 2 * MARGIN - 3 * lh:
            break
    img = Image.new("L", PAGE, 255)
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        d.text((MARGIN, MARGIN + i * lh), l, font=f, fill=0)
    ff = font(22)
    d.text((MARGIN, PAGE[1] - MARGIN), f"{sample_id}   {FOOTER}", font=ff, fill=0)
    return img


def choose(root: Path) -> list[dict]:
    """3 dev documents with different case templates (one with >= 5 medicines), then 2 stress prescriptions."""
    man = json.loads((root / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]
    dev = [d for d in man if d["split"] == "dev"]
    n_meds = lambda d: len(json.loads((root / "data/ground_truth" / f"{d['id']}.json").read_text(encoding="utf-8"))["medications"])  # noqa: E731
    big = max(dev, key=lambda d: (n_meds(d), d["id"]))
    assert n_meds(big) >= 5, "no dev document with 5 or more medicines"
    picks, templates = [big], {big["template"]}
    for d in sorted(dev, key=lambda d: (-n_meds(d), d["id"])):
        if len(picks) == 3:
            break
        if d["template"] not in templates:
            picks.append(d)
            templates.add(d["template"])
    assert len(picks) == 3 and all(d["split"] == "dev" for d in picks)
    rows = [dict(source="dev", id=d["id"], text=root / "data/synthetic" / f"{d['id']}.txt", gt=root / "data/ground_truth" / f"{d['id']}.json", category=f"dev {(d.get('document_type') or d.get('type', 'document')).replace('_', ' ')}, case template {d['template']}, {n_meds(d)} medicines") for d in picks]
    st = json.loads((root / "data/stress/manifest.json").read_text(encoding="utf-8"))["documents"]
    for cat in STRESS_PICKS:
        d = next(x for x in st if x["category"] == cat)
        rows.append(dict(source="stress", id=d["id"], text=root / "data/stress/synthetic" / f"{d['id']}.txt", gt=root / "data/stress/ground_truth" / f"{d['id']}.json", category=f"stress prescription, category {cat}, {d['medicines']} medicines"))
    return rows


def build(root: Path = REPO) -> list[dict]:
    rows = choose(root)
    pages = []
    for k, r in enumerate(rows, 1):
        r["sample"] = f"RP{k}"
        pages.append(page_for(r["text"].read_text(encoding="utf-8"), r["sample"]))
    out = root / "docs" / "real_photo_test"
    out.mkdir(parents=True, exist_ok=True)
    pages[0].save(out / "print_pack.pdf", "PDF", resolution=float(DPI), save_all=True, append_images=pages[1:])
    mp = root / "data" / "real_photos"
    mp.mkdir(parents=True, exist_ok=True)
    (mp / "mapping.json").write_text(json.dumps({r["sample"]: dict(source=r["source"], id=r["id"], text=str(r["text"].relative_to(root)), ground_truth=str(r["gt"].relative_to(root)), category=r["category"]) for r in rows}, indent=1) + "\n", encoding="utf-8", newline="\n")
    (out / "README.md").write_text(
        "# Real-photo test pack\n\nPages of `print_pack.pdf` (A4, one synthetic document per page, black on white). The mapping of RP ids to files is private (gitignored `data/real_photos/mapping.json`); only categories are listed here.\n\n"
        "| id | category |\n|---|---|\n" + "\n".join(f"| {r['sample']} | {r['category'].replace('dev ', 'development document: ', 1) if r['source'] == 'dev' else r['category']} |" for r in rows)
        + "\n\nInstructions: `PROTOCOL.md`. Everything on the pages is fictional.\n", encoding="utf-8", newline="\n")
    return rows


if __name__ == "__main__":
    rows = build()
    print(f"wrote {len(rows)} pages: " + ", ".join(f"{r['sample']} ({r['source']})" for r in rows))
    sys.exit(0)
