"""
MedIntel AI — Security and Authentication Utilities.

Provides password hashing using PBKDF2-HMAC-SHA256, cryptographically
signed JWT-compatible tokens using HMAC-SHA256, and FastAPI dependency
injection for authenticated user resolution.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.models import User

logger = logging.getLogger("medintel.security")

# Secret key for HMAC token signing
_AUTH_SECRET_KEY = getattr(settings, "SECRET_KEY", "medintel-ai-secure-jwt-secret-key-2026")


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored salted PBKDF2 hash."""
    if not plain_password or not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt, expected_hash = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return secrets.compare_digest(key.hex(), expected_hash)
    except Exception as e:
        logger.warning("Error verifying password: %s", str(e))
        return False


def _b64encode_str(data: bytes) -> str:
    """Base64 URL-safe encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode_str(data: str) -> bytes:
    """Base64 URL-safe decode with padding restored."""
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def create_access_token(user_id: int, email: str, expires_in_seconds: int = 86400 * 30) -> str:
    """Generate a signed access token containing user identity and expiration."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + expires_in_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64encode_str(payload_bytes)

    sig = hmac.new(_AUTH_SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = _b64encode_str(sig)

    return f"{payload_b64}.{sig_b64}"


def verify_access_token(token: str) -> Optional[dict]:
    """Verify an access token signature and validity, returning payload or None."""
    if not token or "." not in token:
        return None
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        expected_sig = hmac.new(
            _AUTH_SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256
        ).digest()
        actual_sig = _b64decode_str(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64decode_str(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("exp", 0) < int(time.time()):
            return None

        return payload
    except Exception as e:
        logger.debug("Token verification failed: %s", str(e))
        return None


def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer <token>"),
    x_auth_token: Optional[str] = Header(None, description="Direct token header"),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to extract and validate the currently authenticated user."""
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_auth_token:
        token = x_auth_token.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
