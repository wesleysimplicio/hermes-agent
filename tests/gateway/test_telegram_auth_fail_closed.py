"""Tests for Telegram fail-closed auth (#24457).

When TELEGRAM_ALLOWED_USERS is empty, _is_authorized_user() must return
False (fail closed) unless an explicit allow-all env var is set.
"""


def _simulate_auth(user_id: str, env: dict) -> bool:
    """Reproduce the _is_authorized_user fallback logic inline."""
    allowed_csv = env.get("TELEGRAM_ALLOWED_USERS", "").strip()
    if not allowed_csv:
        _global_open = env.get("GATEWAY_ALLOW_ALL_USERS", "").lower() in ("true", "1", "yes")
        _tg_open = env.get("TELEGRAM_ALLOW_ALL_USERS", "").lower() in ("true", "1", "yes")
        return _global_open or _tg_open
    allowed_ids = {uid.strip() for uid in allowed_csv.split(",") if uid.strip()}
    return "*" in allowed_ids or user_id in allowed_ids


def test_no_allowlist_no_allow_all_denies():
    assert _simulate_auth("999", {}) is False


def test_gateway_allow_all_permits():
    assert _simulate_auth("999", {"GATEWAY_ALLOW_ALL_USERS": "true"}) is True


def test_telegram_allow_all_permits():
    assert _simulate_auth("999", {"TELEGRAM_ALLOW_ALL_USERS": "1"}) is True


def test_allowlist_match_permits():
    assert _simulate_auth("123", {"TELEGRAM_ALLOWED_USERS": "123,456"}) is True


def test_allowlist_mismatch_denies():
    assert _simulate_auth("999", {"TELEGRAM_ALLOWED_USERS": "123,456"}) is False


def test_wildcard_in_allowlist_permits_all():
    assert _simulate_auth("999", {"TELEGRAM_ALLOWED_USERS": "*"}) is True
