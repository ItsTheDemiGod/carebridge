"""Create CAREBRIDGE_DATA_KEY (a Fernet key) in backend/.env if it is not there yet. Never prints the key.   python scripts/generate_data_key.py"""
import re
from pathlib import Path

from cryptography.fernet import Fernet

ENV = Path(__file__).resolve().parents[1] / "backend" / ".env"


def main(env: Path = ENV) -> str:
    text = env.read_text(encoding="utf-8") if env.exists() else ""
    if re.search(r"^\s*CAREBRIDGE_DATA_KEY\s*=\s*\S", text, re.M):
        return "key already present"
    text = re.sub(r"^\s*CAREBRIDGE_DATA_KEY\s*=\s*$\n?", "", text, flags=re.M)  # an empty placeholder line is replaced
    with env.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text + ("" if text.endswith("\n") or not text else "\n") + f"CAREBRIDGE_DATA_KEY={Fernet.generate_key().decode()}\n")
    return "key created"


if __name__ == "__main__":
    print(main())
