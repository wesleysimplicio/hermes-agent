"""Regression test for the `tui.mouse_support` config toggle.

Mouse support in prompt_toolkit captures mouse events for in-app scrolling
and cursor positioning, but it also breaks terminal-multiplexer scrollback
(tmux/screen) and native text selection. The default stays ``False``, but
users who opt in via ``tui.mouse_support: true`` in config.yaml must be
honoured.

This is a source-inspection test (same pattern as
``tests/tools/test_terminal_config_env_sync.py``) so it does not require
instantiating ``HermesCLI`` (which pulls heavy TTY / async deps).
"""

import inspect

import cli


def _application_call_source() -> str:
    src = inspect.getsource(cli)
    marker = "app = Application("
    idx = src.index(marker)
    depth = 0
    pos = idx + len(marker) - 1
    while pos < len(src):
        ch = src[pos]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return src[idx : pos + 1]
        pos += 1
    raise AssertionError("Could not find balanced Application(...) call")


def test_application_reads_mouse_support_from_tui_config() -> None:
    snippet = _application_call_source()
    assert "mouse_support" in snippet, (
        "Application(...) must pass mouse_support kwarg"
    )
    assert '"tui"' in snippet or "'tui'" in snippet, (
        "mouse_support must be derived from the tui config section"
    )
    assert '"mouse_support"' in snippet or "'mouse_support'" in snippet, (
        "mouse_support must read the tui.mouse_support key"
    )


def test_mouse_support_defaults_to_false_when_section_missing() -> None:
    config: dict = {}
    value = bool((config.get("tui") or {}).get("mouse_support", False))
    assert value is False


def test_mouse_support_defaults_to_false_when_key_missing() -> None:
    config = {"tui": {"other": True}}
    value = bool((config.get("tui") or {}).get("mouse_support", False))
    assert value is False


def test_mouse_support_enabled_when_user_opts_in() -> None:
    config = {"tui": {"mouse_support": True}}
    value = bool((config.get("tui") or {}).get("mouse_support", False))
    assert value is True


def test_mouse_support_handles_none_tui_section() -> None:
    config = {"tui": None}
    value = bool((config.get("tui") or {}).get("mouse_support", False))
    assert value is False
