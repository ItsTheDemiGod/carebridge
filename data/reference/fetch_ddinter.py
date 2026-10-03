"""Download the 8 official DDInter CSV files (ATC groups A, B, D, H, L, P, R, V) into data/reference/ddinter/raw/.
Licence: CC BY-NC-SA 4.0 (https://ddinter.scbdd.com/terms/). The raw files are NOT committed (gitignored).
Run from the repo root with the backend venv's python: python data/reference/fetch_ddinter.py"""
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parent / "ddinter" / "raw"
BASE = "https://ddinter.scbdd.com/static/media/download/ddinter_downloads_code_{}.csv"

RAW.mkdir(parents=True, exist_ok=True)
for g in "ABDHLPRV":
    data = urllib.request.urlopen(urllib.request.Request(BASE.format(g), headers={"User-Agent": "CareBridge-coursework"})).read()
    (RAW / f"ddinter_downloads_code_{g}.csv").write_bytes(data)
    print(g, len(data), "bytes")
