import base64
import os
import uuid
from typing import Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes


def _derive_key_from_env(secret_value: str, length_bytes: int = 16) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(secret_value.encode("utf-8"))
    full = digest.finalize()
    return full[:length_bytes]


def _get_aes_key() -> bytes:
    secret: Optional[str] = os.getenv("SHARE_TOKEN_KEY") or os.getenv("SECRET_KEY")
    if not secret:
        # Development fallback; set SHARE_TOKEN_KEY in production
        secret = "cv-generator-dev-share-token-key"
    return _derive_key_from_env(secret, 16)


def _aes_ecb_encrypt_block(key: bytes, block16: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(block16) + encryptor.finalize()


def _aes_ecb_decrypt_block(key: bytes, block16: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(block16) + decryptor.finalize()


def encode_share_token(resume_id: str) -> str:
    uuid_obj = uuid.UUID(resume_id)
    key = _get_aes_key()
    ciphertext = _aes_ecb_encrypt_block(key, uuid_obj.bytes)
    token = base64.urlsafe_b64encode(ciphertext).rstrip(b"=")
    return token.decode("ascii")


def decode_share_token(token: str) -> str:
    padding_len = (-len(token)) % 4
    padded = token + ("=" * padding_len)
    data = base64.urlsafe_b64decode(padded.encode("ascii"))
    if len(data) != 16:
        raise ValueError("Invalid token length")
    key = _get_aes_key()
    plain = _aes_ecb_decrypt_block(key, data)
    uuid_obj = uuid.UUID(bytes=plain)
    return str(uuid_obj)


