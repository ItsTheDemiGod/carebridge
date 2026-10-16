import sys

from cryptography.fernet import Fernet

from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import generate_data_key as G  # noqa: E402


def test_creates_once_and_never_prints(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("LLM_PROVIDER=ollama\nCAREBRIDGE_DATA_KEY=\n", encoding="utf-8")
    assert G.main(env) == "key created"
    lines = env.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "LLM_PROVIDER=ollama" and len([x for x in lines if x.startswith("CAREBRIDGE_DATA_KEY=")]) == 1
    key = lines[-1].split("=", 1)[1]
    Fernet(key)  # valid
    assert G.main(env) == "key already present"
    assert env.read_text(encoding="utf-8").count(key) == 1
    assert key not in capsys.readouterr().out


def test_creates_file_when_missing(tmp_path):
    env = tmp_path / ".env"
    assert G.main(env) == "key created" and env.read_text(encoding="utf-8").startswith("CAREBRIDGE_DATA_KEY=")
