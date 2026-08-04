"""Password security helpers for IntelliCrew.

Passwords created by seed_data.py are stored as:
    scrypt$<salt_hex>$<digest_hex>

Password hashing is one-way. There is deliberately no decrypt_password()
function. Login verifies the entered password against the stored hash.
"""

import hashlib
import hmac
import secrets


def hash_password(plain_password: str) -> str:
    """Create a salted scrypt hash for a new or changed password."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        plain_password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64,
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
            n=2**14,
            r=8,
            p=1,
            dklen=64,
        )
        return hmac.compare_digest(
            actual_digest.hex(),
            expected_digest_hex,
        )
    except (AttributeError, TypeError, ValueError):
        return False
