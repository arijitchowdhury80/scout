"""Tests for hosted API key lifecycle primitives.

# Scenario list:
# - generated keys use a Scout prefix and enough entropy
# - hashing is deterministic for the same key and does not reveal the raw key
# - verification accepts the matching raw key
# - verification rejects wrong raw keys
# - masked keys preserve only prefix and tail
# - active key metadata is usable
# - revoked key metadata is not usable
"""

from __future__ import annotations

from scout.core.platform.api_keys import (
    ApiKeyRecord,
    ApiKeyStatus,
    generate_api_key,
    hash_api_key,
    is_key_usable,
    mask_api_key,
    verify_api_key,
)


def test_generate_api_key_uses_scout_prefix_and_entropy() -> None:
    key = generate_api_key()

    assert key.startswith("scout_live_")
    assert len(key) >= 40
    assert key != generate_api_key()


def test_hash_api_key_is_deterministic_without_revealing_raw_key() -> None:
    raw_key = "scout_live_test_secret"

    digest = hash_api_key(raw_key)

    assert digest == hash_api_key(raw_key)
    assert raw_key not in digest


def test_verify_api_key_accepts_matching_raw_key() -> None:
    raw_key = "scout_live_test_secret"

    assert verify_api_key(raw_key, hash_api_key(raw_key)) is True


def test_verify_api_key_rejects_wrong_raw_key() -> None:
    digest = hash_api_key("scout_live_test_secret")

    assert verify_api_key("scout_live_wrong", digest) is False


def test_mask_api_key_preserves_prefix_and_tail_only() -> None:
    masked = mask_api_key("scout_live_abcdefghijklmnopqrstuvwxyz")

    assert masked.startswith("scout_live_")
    assert masked.endswith("wxyz")
    assert "abcdefghijklmnopqrstuv" not in masked


def test_is_key_usable_accepts_active_record_with_scope() -> None:
    record = ApiKeyRecord(
        key_id="key_123",
        tenant_id="tenant_123",
        key_hash=hash_api_key("scout_live_test_secret"),
        name="Default key",
        scopes=["runs:create"],
        status=ApiKeyStatus.ACTIVE,
    )

    assert is_key_usable(record, required_scope="runs:create") is True


def test_is_key_usable_rejects_revoked_record() -> None:
    record = ApiKeyRecord(
        key_id="key_123",
        tenant_id="tenant_123",
        key_hash=hash_api_key("scout_live_test_secret"),
        name="Default key",
        scopes=["runs:create"],
        status=ApiKeyStatus.REVOKED,
    )

    assert is_key_usable(record, required_scope="runs:create") is False
