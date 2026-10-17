"""Phase 6c-1: original favicon from the wordmark's bridge-arch motif. Writes frontend/public/{favicon.svg,favicon-32.png,apple-touch-icon.png,icon-192.png,icon-512.png}.
Pillow only (no new dependency). python scripts/make_favicons.py"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "frontend" / "public"
PAPER, PINE, TERRA = "#f5efe3", "#1e4d45", "#c4572f"
TY, SW = 6, 2.2  # shift the 40x30 wordmark into a 40x40 square; stroke width (units of 40)
ARCS = [((5, 25.5), (5, 11), (35, 11), (35, 25.5)), ((11, 25.5), (11, 17.5), (29, 17.5), (29, 25.5)), ((17, 25.5), (17, 21.5), (23, 21.5), (23, 25.5))]

SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="8" fill="{PAPER}"/><g transform="translate(0 {TY})" fill="none" stroke="{PINE}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 25.5h37"/><path d="M5 25.5C5 11 35 11 35 25.5"/><path d="M11 25.5c0-8 18-8 18 0"/><path d="M17 25.5c0-4 6-4 6 0"/><path d="M20 3v6M17 6h6" stroke="{TERRA}"/></g></svg>
"""


def bez(p, n=60):
    return [tuple((1 - t) ** 3 * p[0][i] + 3 * (1 - t) ** 2 * t * p[1][i] + 3 * (1 - t) * t * t * p[2][i] + t ** 3 * p[3][i] for i in (0, 1)) for t in (k / n for k in range(n + 1))]


def render(size: int) -> Image.Image:
    s = size * 4 / 40  # 4x supersampling
    im = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1], radius=8 * s, fill=PAPER)

    def line(pts, col):
        pts = [(x * s, (y + TY) * s) for x, y in pts]
        w = SW * s
        d.line(pts, fill=col, width=round(w), joint="curve")
        for x, y in (pts[0], pts[-1]):
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)

    line([(1.5, 25.5), (38.5, 25.5)], PINE)
    for a in ARCS:
        line(bez(a), PINE)
    line([(20, 3), (20, 9)], TERRA)
    line([(17, 6), (23, 6)], TERRA)
    return im.resize((size, size), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "favicon.svg").write_text(SVG, encoding="utf-8", newline="\n")
    for name, size in (("favicon-32.png", 32), ("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)):
        render(size).save(OUT / name, optimize=True)
    print("favicons written")


if __name__ == "__main__":
    main()
