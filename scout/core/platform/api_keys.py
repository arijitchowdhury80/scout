"""Hosted API key lifecycle primitives."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

_KEY_PREFIX = "scout_live_"


class ApiKeyStatus(str, Enum):
    """API key lifecycle status."""

    ACTIVE = "active"
    REVOKED = "revoked"
    DISABLED = "disabled"


class ApiKeyRecord(BaseModel):
    """Stored API key metadata; never stores the raw API key."""

    key_id: str
    tenant_id: str
    key_hash: str
    name: str = ""
    scopes: list[str] = Field(default_factory=list)
    status: ApiKeyStatus = ApiKeyStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_used_at: str = ""


def generate_api_key() -> str:
    """Generate a hosted Scout API key for one-time display."""
    return f"{_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Verify a raw API key against a stored hash."""
    return hmac.compare_digest(hash_api_key(raw_key), stored_hash)


def mask_api_key(raw_key: str) -> str:
    """Return a display-safe API key mask."""
    if len(raw_key) <= len(_KEY_PREFIX) + 4:
        return f"{_KEY_PREFIX}****"
    return f"{_KEY_PREFIX}...{raw_key[-4:]}"


def is_key_usable(record: ApiKeyRecord, required_scope: str = "") -> bool:
    """Return whether an API key record can be used for a scope."""
    if record.status is not ApiKeyStatus.ACTIVE:
        return False
    if required_scope and required_scope not in record.scopes:
        return False
    return True
