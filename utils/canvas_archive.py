from __future__ import annotations

import base64
import hashlib
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

FORMAT_VERSION = 1
NONCE_SIZE = 12
TAG_SIZE = 16


def encode_bytes(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def decode_bytes(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def archive_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derive_key(password: str, salt: bytes) -> bytes:
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(password.encode("utf-8"))


def encrypt_bytes(data: bytes, key: bytes, nonce: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    nonce = nonce or os.urandom(NONCE_SIZE)
    encrypted = AESGCM(key).encrypt(nonce, data, None)
    return nonce, encrypted[:-TAG_SIZE], encrypted[-TAG_SIZE:]


def decrypt_bytes(ciphertext: bytes, tag: bytes, nonce: bytes, key: bytes) -> bytes:
    return AESGCM(key).decrypt(nonce, ciphertext + tag, None)


def encode_plain_metadata(metadata: dict) -> bytes:
    return json.dumps({"format_version": FORMAT_VERSION, "encrypted": False, "metadata": metadata}, indent=2).encode("utf-8") + b"\n"


def encode_encrypted_metadata(metadata: dict, password: str, salt: bytes, key: bytes) -> bytes:
    payload = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    nonce, ciphertext, tag = encrypt_bytes(payload, key)
    envelope = {
        "format_version": FORMAT_VERSION,
        "encrypted": True,
        "kdf": {"name": "scrypt", "salt": encode_bytes(salt), "n": 2**14, "r": 8, "p": 1},
        "nonce": encode_bytes(nonce),
        "ciphertext": encode_bytes(ciphertext),
        "tag": encode_bytes(tag),
    }
    return json.dumps(envelope, indent=2).encode("utf-8") + b"\n"


def decode_metadata(envelope: bytes, password: str | None) -> tuple[dict, bytes | None]:
    try:
        container = json.loads(envelope)
        if container.get("format_version") != FORMAT_VERSION:
            raise ValueError("unsupported canvas archive format")
        if not container.get("encrypted"):
            return container["metadata"], None
        if password is None:
            raise ValueError("archive is encrypted; provide a password")
        kdf = container["kdf"]
        key = derive_key(password, decode_bytes(kdf["salt"]))
        payload = decrypt_bytes(decode_bytes(container["ciphertext"]), decode_bytes(container["tag"]), decode_bytes(container["nonce"]), key)
        return json.loads(payload), key
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("could not authenticate metadata; password may be incorrect") from exc