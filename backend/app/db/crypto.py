"""Authenticated encryption of stored payloads (Fernet = AES-128-CBC + HMAC-SHA256).

The document id and the payload kind sit INSIDE the encrypted envelope and are checked on decrypt, so a blob copied to another
document row (or another kind) is rejected even though it is a valid Fernet token. Images are base64 inside the envelope."""
import base64
import json

from cryptography.fernet import Fernet, InvalidToken


class CryptoError(Exception):
    """Bad key, tampered blob, or a blob that does not belong to this row. Never carries content."""


class Vault:
    def __init__(self, key: str | bytes):
        try:
            self._f = Fernet(key)
        except (ValueError, TypeError):
            raise CryptoError("CAREBRIDGE_DATA_KEY is not a valid Fernet key")

    def seal(self, document_id: str, kind: str, value) -> bytes:
        v = {"b64": base64.b64encode(value).decode()} if isinstance(value, (bytes, bytearray)) else {"json": value}
        return self._f.encrypt(json.dumps({"d": document_id, "k": kind, "v": v}, ensure_ascii=False).encode())

    def open(self, document_id: str, kind: str, blob: bytes):
        try:
            env = json.loads(self._f.decrypt(bytes(blob)))
        except (InvalidToken, ValueError):
            raise CryptoError("payload cannot be decrypted")
        if env.get("d") != document_id or env.get("k") != kind:
            raise CryptoError("payload belongs to another row")
        v = env["v"]
        return base64.b64decode(v["b64"]) if "b64" in v else v["json"]
