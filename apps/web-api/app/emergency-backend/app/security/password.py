from __future__ import annotations
import hashlib, hmac

# Try bcrypt via passlib; fall back to dev SHA256 if anything fails.
_HAS_BCRYPT = True
try:
    from passlib.context import CryptContext  # type: ignore
    _ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception:
    _HAS_BCRYPT = False
    _ctx = None  # type: ignore

# Simple dev salt for fallback hashing (DO NOT use in production)
_DEV_SALT = b"ers-dev-fallback-salt"


def _sha256_dev(pw: str) -> str:
    digest = hashlib.sha256(_DEV_SALT + pw.encode("utf-8")).hexdigest()
    return "sha256$" + digest


def hash_password(pw: str) -> str:
    """
    Hash with bcrypt if healthy; otherwise fallback to deterministic dev sha256.
    Also guards against bcrypt's 72-byte limit by truncating input.
    """
    if _HAS_BCRYPT and _ctx is not None:
        try:
            return _ctx.hash(pw[:72])  # bcrypt safe length
        except Exception:
            # Any backend/self-test error -> fallback
            return _sha256_dev(pw)
    return _sha256_dev(pw)


def verify_password(pw: str, stored: str) -> bool:
    """
    Verify bcrypt, dev sha256, or plaintext (for dev/seed).
    """
    if not isinstance(stored, str) or not stored:
        return False

    # Plaintext (used by some dev seeds)
    if not stored.startswith("$") and not stored.startswith("sha256$"):
        return hmac.compare_digest(stored, pw)

    # Dev sha256 fallback
    if stored.startswith("sha256$"):
        return hmac.compare_digest(stored, _sha256_dev(pw))

    # bcrypt
    if _HAS_BCRYPT and _ctx is not None and stored.startswith("$2"):
        try:
            return _ctx.verify(pw, stored)
        except Exception:
            return False

    return False
