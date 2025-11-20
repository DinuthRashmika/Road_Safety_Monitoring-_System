from __future__ import annotations
import hashlib, hmac

_HAS_BCRYPT = True
try:
    from passlib.context import CryptContext  
    _ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception:
    _HAS_BCRYPT = False
    _ctx = None  

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
            return _ctx.hash(pw[:72]) 
        except Exception:
            return _sha256_dev(pw)
    return _sha256_dev(pw)


def verify_password(pw: str, stored: str) -> bool:
    """
    Verify bcrypt, dev sha256, or plaintext (for dev/seed).
    """
    if not isinstance(stored, str) or not stored:
        return False

    if not stored.startswith("$") and not stored.startswith("sha256$"):
        return hmac.compare_digest(stored, pw)

    if stored.startswith("sha256$"):
        return hmac.compare_digest(stored, _sha256_dev(pw))

    if _HAS_BCRYPT and _ctx is not None and stored.startswith("$2"):
        try:
            return _ctx.verify(pw, stored)
        except Exception:
            return False

    return False
