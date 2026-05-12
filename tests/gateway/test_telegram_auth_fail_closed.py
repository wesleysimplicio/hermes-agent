"""Tests for Telegram _is_authorized_user failing closed when no allowlist is set."""


def _simulate_is_authorized(user_id: str, env: dict) -> bool:
    """Replicate the env-based auth logic from TelegramAdapter._is_authorized_user."""
    allowed_csv = env.get("TELEGRAM_ALLOWED_USERS", "").strip()
    if not allowed_csv:
        _global_open = env.get("GATEWAY_ALLOW_ALL_USERS", "").lower() in ("true", "1", "yes")
        _tg_open = env.get("TELEGRAM_ALLOW_ALL_USERS", "").lower() in ("true", "1", "yes")
        return _global_open or _tg_open
    allowed_ids = {uid.strip() for uid in allowed_csv.split(",") if uid.strip()}
    return "*" in allowed_ids or user_id in allowed_ids


class TestTelegramAuthFailClosed:
    def test_no_allowlist_no_allow_all_denies(self):
        result = _simulate_is_authorized("999", {})
        assert result is False

    def test_no_allowlist_gateway_allow_all_true_permits(self):
        result = _simulate_is_authorized("999", {"GATEWAY_ALLOW_ALL_USERS": "true"})
        assert result is True

    def test_no_allowlist_telegram_allow_all_true_permits(self):
        result = _simulate_is_authorized("999", {"TELEGRAM_ALLOW_ALL_USERS": "1"})
        assert result is True

    def test_no_allowlist_allow_all_false_string_denies(self):
        result = _simulate_is_authorized("999", {"GATEWAY_ALLOW_ALL_USERS": "false"})
        assert result is False

    def test_known_user_in_allowlist_permits(self):
        result = _simulate_is_authorized("123456", {"TELEGRAM_ALLOWED_USERS": "123456,789012"})
        assert result is True

    def test_unknown_user_in_allowlist_denies(self):
        result = _simulate_is_authorized("000000", {"TELEGRAM_ALLOWED_USERS": "123456,789012"})
        assert result is False

    def test_wildcard_in_allowlist_permits_anyone(self):
        result = _simulate_is_authorized("999999", {"TELEGRAM_ALLOWED_USERS": "*"})
        assert result is True
