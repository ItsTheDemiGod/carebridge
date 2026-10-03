r"""Send one tiny text prompt to Gemini. Prints only OK/FAIL and the error type, never the key.
Run from backend/:  .venv\Scripts\python scripts\smoke_test_gemini.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402

if not settings.gemini_api_key:
    print("FAIL: GEMINI_API_KEY not set")
    sys.exit(1)
try:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)  # keep a reference: a temporary client is closed on GC
    r = client.models.generate_content(model=settings.gemini_model, contents="Reply with the single word: ok")
    print("OK" if r.text else "FAIL: empty response", settings.gemini_model)
except Exception as e:  # noqa: BLE001
    print("FAIL:", type(e).__name__, getattr(e, "code", ""))
    sys.exit(1)
