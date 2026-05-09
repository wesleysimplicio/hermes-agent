"""Regression for #22401: scripts/run_tests.sh must work in uv-created venvs
without pip.

The script self-installs ``pytest-split`` when it's missing. The original
implementation called ``"$PYTHON" -m pip install`` unconditionally — which
fails in a uv-managed venv where pip is not present, exiting before any
test runs.

These are static guards on the script text (no subprocess required): the
bootstrap block must declare the dependency in pyproject's ``dev`` extra
*and* fall back from pip → uv when pip is missing rather than aborting.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_TESTS_SH = REPO_ROOT / "scripts" / "run_tests.sh"
PYPROJECT = REPO_ROOT / "pyproject.toml"


@pytest.fixture(scope="module")
def script_text() -> str:
    return RUN_TESTS_SH.read_text()


@pytest.fixture(scope="module")
def pyproject_text() -> str:
    return PYPROJECT.read_text()


def test_pytest_split_declared_in_dev_extra(pyproject_text: str) -> None:
    """The dev extra must list pytest-split so a fresh `uv sync --extra dev`
    or `pip install -e '.[dev]'` brings it in without an ad-hoc bootstrap.
    """
    dev_line = next(
        (
            line
            for line in pyproject_text.splitlines()
            if line.lstrip().startswith("dev =")
        ),
        None,
    )
    assert dev_line is not None, "could not find dev = [...] in pyproject.toml"
    assert "pytest-split" in dev_line, (
        f"dev extra must declare pytest-split (#22401); got: {dev_line}"
    )


def _bootstrap_block(script_text: str) -> str:
    block_match = re.search(
        r"if\s+!\s+\"\$PYTHON\"\s+-c\s+\"import pytest_split\".*?\nfi\n",
        script_text,
        flags=re.DOTALL,
    )
    assert block_match, "could not locate pytest_split bootstrap block"
    return block_match.group(0)


def test_bootstrap_falls_back_to_uv_when_pip_missing(script_text: str) -> None:
    """In a uv-created venv without pip, calling ``python -m pip install``
    crashes with ``No module named pip`` and the script aborts before any
    test runs. The bootstrap must probe pip first and fall back to ``uv pip
    install`` when pip isn't available.
    """
    block = _bootstrap_block(script_text)

    assert '"$PYTHON" -m pip --version' in block, (
        "bootstrap must probe `pip --version` before invoking `pip install`"
    )

    assert "uv pip install" in block, (
        "bootstrap must fall back to `uv pip install` when pip is missing"
    )


def test_bootstrap_emits_actionable_error_when_neither_available(
    script_text: str,
) -> None:
    """If neither pip nor uv is available, the script must exit non-zero
    with a clear message rather than running pytest with the missing dep.
    """
    block = _bootstrap_block(script_text)
    assert "exit 1" in block, (
        "bootstrap must exit non-zero when pytest-split cannot be installed"
    )
