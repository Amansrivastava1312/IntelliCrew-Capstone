"""Password security helpers for IntelliCrew.

Passwords created by data_seed.py are stored as:
    scrypt$<salt_hex>$<digest_hex>

Password hashing is one-way. There is deliberately no decrypt_password()
function. Login verifies the entered password against the stored hash.
"""

import hashlib
import hmac
import secrets


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 64
SALT_SIZE = 16


def hash_password(plain_password: str) -> str:
    """Create a salted scrypt hash for a new or changed password."""
    salt = secrets.token_bytes(SALT_SIZE)
    digest = hashlib.scrypt(
        plain_password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Return True when plain_password matches stored_hash."""
    try:
        algorithm, salt_hex, expected_digest_hex = stored_hash.split("$")
        if algorithm != "scrypt":
            return False

        actual_digest = hashlib.scrypt(
            plain_password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            dklen=SCRYPT_DKLEN,
        )
        return hmac.compare_digest(
            actual_digest.hex(),
            expected_digest_hex,
        )
    except (AttributeError, TypeError, ValueError):
        return False
