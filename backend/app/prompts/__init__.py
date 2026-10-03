from pathlib import Path

PROMPT_VERSION = "v1"
PROMPT_DIR = Path(__file__).parent


def load_prompt(version: str = PROMPT_VERSION) -> str:
    return (PROMPT_DIR / f"extraction_{version}.txt").read_text(encoding="utf-8")
