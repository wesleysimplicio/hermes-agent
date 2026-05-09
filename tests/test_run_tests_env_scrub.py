"""Regression: `scripts/run_tests.sh` must scrub scheduler-injected
HERMES_CRON_SESSION before running pytest.

Without this, running the canonical test runner from a Hermes cron job
leaks cron approval mode into the test process and flips approval
callbacks to deny — making interactive-callback tests fail only under
cron (#22400).
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_TESTS = REPO_ROOT / "scripts" / "run_tests.sh"


def test_run_tests_script_scrubs_hermes_cron_session():
    body = RUN_TESTS.read_text(encoding="utf-8")

    # Extract the `unset HERMES_*` stanza (with bash line continuations) and
    # assert the variable appears in that block — not just anywhere in the
    # file, otherwise a comment mentioning it would silently pass.
    match = re.search(
        r"^unset\s+HERMES_[A-Za-z0-9_ \\\n\t]+",
        body,
        flags=re.MULTILINE,
    )
    assert match, "scripts/run_tests.sh must contain an `unset HERMES_*` stanza"

    unset_block = match.group(0)
    assert re.search(r"\bHERMES_CRON_SESSION\b", unset_block), (
        "scripts/run_tests.sh must unset HERMES_CRON_SESSION (in the `unset` "
        "block, not just in a comment) so cron approval mode does not leak "
        "into pytest (#22400)"
    )
