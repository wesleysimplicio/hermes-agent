"""Regression: `scripts/run_tests.sh` must scrub scheduler-injected
HERMES_CRON_SESSION before running pytest.

Without this, running the canonical test runner from a Hermes cron job
leaks cron approval mode into the test process and flips approval
callbacks to deny — making interactive-callback tests fail only under
cron (#22400).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_TESTS = REPO_ROOT / "scripts" / "run_tests.sh"


def test_run_tests_script_scrubs_hermes_cron_session():
    body = RUN_TESTS.read_text(encoding="utf-8")

    # Confined to the explicit `unset HERMES_*` block — string-search the
    # variable name is enough and lets contributors reorder the list freely.
    assert "HERMES_CRON_SESSION" in body, (
        "scripts/run_tests.sh must unset HERMES_CRON_SESSION so cron "
        "approval mode does not leak into pytest (#22400)"
    )
