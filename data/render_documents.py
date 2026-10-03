"""Render the 60 synthetic .txt documents into images under data/rendered/<condition>/<id>.png.

Conditions: clean, scan, photo, poor. PDFs (clean, scan) go to data/rendered/<condition>/<id>.pdf.
Deterministic: fixed seed per (document, condition); Pillow + numpy only.
Run from the repo root:  backend\\.venv\\Scripts\\python data\\render_documents.py
"""

import io
import json
import time
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "rendered"
SEED = 7
CONDITIONS = ["clean", "scan", "photo", "poor"]
FONT_SIZE, MARGIN, LINE_H = 22, 48, 30
FONT_CANDIDATES = ["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]


def load_font():
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return ImageFont.truetype(f, FONT_SIZE)
    return ImageFont.load_default(size=FONT_SIZE)


def draw_page(text, font):
    """Return (page image 'L', ink mask 'L'): text black on white, and 255 where ink was drawn."""
    lines = text.split("\n")
    w = int(max(font.getlength(l) for l in lines)) + 2 * MARGIN
    h = len(lines) * LINE_H + 2 * MARGIN  # long documents simply get a taller page
    page, ink = Image.new("L", (max(w, 700), h), 255), Image.new("L", (max(w, 700), h), 0)
    dp, di = ImageDraw.Draw(page), ImageDraw.Draw(ink)
    for i, l in enumerate(lines):
        xy = (MARGIN, MARGIN + i * LINE_H)
        dp.text(xy, l, font=font, fill=20)
        di.text(xy, l, font=font, fill=255)
    return page, ink


def pad(img, p, fill):
    out = Image.new("L", (img.width + 2 * p, img.height + 2 * p), fill)
    out.paste(img, (p, p))
    return out


def shadow(shape, lo, rng):
    """Uneven lighting: linear gradient in a random direction from lo..1."""
    h, w = shape
    a = rng.uniform(0, 2 * np.pi)
    yy, xx = np.mgrid[0:h, 0:w]
    t = (xx * np.cos(a) + yy * np.sin(a)) / max(h, w)
    t = (t - t.min()) / (np.ptp(t) + 1e-9)
    return lo + (1 - lo) * t, a


def jpeg(img, q):
    b = io.BytesIO()
    img.save(b, "JPEG", quality=q)
    return Image.open(io.BytesIO(b.getvalue())).convert("L")


def perspective_coeffs(w, h, d):
    """Map output corners to slightly moved input corners (mild skew)."""
    src = [(d[0], d[1]), (w - d[2], d[3]), (w - d[4], h - d[5]), (d[6], h - d[7])]
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    A = []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
    sol = np.linalg.solve(np.array(A, float), np.array([c for p in src for c in p], float))
    return tuple(sol)


def geometry(page, ink, rng, max_rot, skew):
    """Rotate (and optionally skew) page and ink mask identically; returns images and parameters."""
    p = int(0.12 * max(page.size))  # padding so rotation/skew never cuts text
    page, ink = pad(page, p, 255), pad(ink, p, 0)
    ang = float(rng.uniform(-max_rot, max_rot))
    page, ink = page.rotate(ang, Image.BICUBIC, expand=True, fillcolor=255), ink.rotate(ang, Image.BICUBIC, expand=True, fillcolor=0)
    params = {"rotation_deg": round(ang, 3)}
    if skew:
        d = [float(x) for x in rng.uniform(0, skew * min(page.size), 8)]
        c = perspective_coeffs(*page.size, d)
        page, ink = page.transform(page.size, Image.PERSPECTIVE, c, Image.BICUBIC, fillcolor=255), ink.transform(ink.size, Image.PERSPECTIVE, c, Image.BICUBIC, fillcolor=0)
        params["skew_px"] = [round(x, 1) for x in d]
    return page, ink, params


def render(text, cond, doc_id, font):
    rng = np.random.default_rng([SEED, zlib.crc32(f"{doc_id}-{cond}".encode())])
    page, ink = draw_page(text, font)
    params = {}
    if cond == "scan":
        page, ink, params = geometry(page, ink, rng, 1.5, 0)
        a = np.asarray(page.filter(ImageFilter.GaussianBlur(0.6)), float) * 0.93  # grey paper
        a += rng.normal(0, 5, a.shape)
        page = jpeg(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), 75)
        params.update(blur=0.6, noise_sigma=5, jpeg_q=75)
    elif cond == "photo":
        page, ink, params = geometry(page, ink, rng, 4, 0.03)
        sh, ang = shadow(np.asarray(page).shape, 0.62, rng)
        a = np.asarray(page, float) * 0.92 * sh + rng.normal(0, 4, sh.shape)
        page = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        ink = ink.resize((int(ink.width * 0.6), int(ink.height * 0.6)), Image.BILINEAR)
        page = jpeg(page.resize(ink.size, Image.LANCZOS), 55)
        params.update(shadow_lo=0.62, scale=0.6, jpeg_q=55)
    elif cond == "poor":
        page, ink, params = geometry(page, ink, rng, 2, 0.02)
        sh, _ = shadow(np.asarray(page).shape, 0.35, rng)
        a = np.asarray(page.filter(ImageFilter.GaussianBlur(1.4)), float)
        a = 150 + (a - 150) * 0.55  # low contrast
        page = Image.fromarray(np.clip(a * sh, 0, 255).astype(np.uint8))
        small = (int(page.width * 0.5), int(page.height * 0.5))
        page = jpeg(page.resize(small, Image.BILINEAR).resize(page.size, Image.BILINEAR), 45)
        params.update(blur=1.4, down_up=0.5, contrast=0.55, shadow_lo=0.35, jpeg_q=45)
    assert_in_bounds(ink, doc_id, cond)
    return page, params


def assert_in_bounds(ink, doc_id, cond):
    a = np.asarray(ink)
    border = np.concatenate([a[:3].ravel(), a[-3:].ravel(), a[:, :3].ravel(), a[:, -3:].ravel()])
    assert a.max() > 0 and not border.any(), f"text touches image edge: {doc_id} {cond}"


def make_preview(doc_id="rx_001", width=520):
    """One small committed image: one document under all four conditions, side by side."""
    ims = []
    for cond in CONDITIONS:
        im = Image.open(OUT / cond / f"{doc_id}.png").convert("L")
        ims.append(im.resize((width, int(im.height * width / im.width)), Image.LANCZOS))
    h = max(i.height for i in ims)
    sheet = Image.new("L", (width * 4 + 5 * 10, h + 20), 120)
    for k, im in enumerate(ims):
        sheet.paste(im, (10 + k * (width + 10), 10))
    dest = ROOT.parent / "docs" / "samples" / "render_preview.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, optimize=True)


def main(limit=None):
    font = load_font()
    docs = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["documents"][:limit]
    entries = []
    for d in docs:
        text = (ROOT / "synthetic" / f"{d['id']}.txt").read_text(encoding="utf-8")
        for cond in CONDITIONS:
            img, params = render(text, cond, d["id"], font) if cond != "clean" else (draw_page(text, font)[0], {})
            (OUT / cond).mkdir(parents=True, exist_ok=True)
            img.save(OUT / cond / f"{d['id']}.png")
            files = [f"{cond}/{d['id']}.png"]
            if cond in ("clean", "scan"):
                img.save(OUT / cond / f"{d['id']}.pdf", "PDF", resolution=150.0, creationDate=time.gmtime(0), modDate=time.gmtime(0))  # fixed dates keep the PDF deterministic
                files.append(f"{cond}/{d['id']}.pdf")
            entries.append(dict(id=d["id"], condition=cond, files=files, size=list(img.size), parameters=params))
    (OUT / "manifest.json").write_text(json.dumps(dict(seed=SEED, font_size=FONT_SIZE, renders=entries), indent=1) + "\n", encoding="utf-8", newline="\n")
    if limit is None:
        make_preview()
    print(f"rendered {len(entries)} images")


if __name__ == "__main__":
    main()
