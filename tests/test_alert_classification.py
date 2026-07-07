"""Tests for classify_pty_alert() embedded in install.py's wrapper_code template.

Verifies the transient-vs-terminal split: rate limit / overloaded are retried by
Claude itself and must NOT kill the session, while billing/credit/weekly/5-hour/
session/auth are terminal and must. The function lives inside a triple-quoted
string written verbatim to /usr/local/bin/claude-telegram-bot, so we extract and
exec it rather than importing.
"""
import re
from pathlib import Path

INSTALL_PY = Path(__file__).resolve().parent.parent / "install.py"


def _load_classify_pty_alert():
    src = INSTALL_PY.read_text("utf-8")
    m = re.search(r"(def classify_pty_alert\(.*?)\n\ndef delete_thinking_message", src, re.S)
    assert m, "classify_pty_alert not found in install.py wrapper_code"
    ns = {"re": re}
    exec(m.group(1), ns)
    return ns["classify_pty_alert"]


classify_pty_alert = _load_classify_pty_alert()


# --- transient: must NOT kill (Claude retries and answers) -------------------

def test_rate_limit_is_transient_not_killed():
    alert, kill, is_auth, no_conv = classify_pty_alert("... API Error: RateLimitError ...")
    assert alert is not None
    assert kill is False
    assert is_auth is False
    assert no_conv is False


def test_overloaded_is_transient_not_killed():
    alert, kill, _, _ = classify_pty_alert("... OverloadedError: servers busy ...")
    assert alert is not None
    assert kill is False


# --- terminal: must kill -----------------------------------------------------

def test_billing_limit_is_terminal():
    _, kill, _, _ = classify_pty_alert("... billing limit reached ...")
    assert kill is True


def test_credit_balance_is_terminal():
    _, kill, _, _ = classify_pty_alert("... your credit balance too low ...")
    assert kill is True


def test_weekly_limit_is_terminal():
    _, kill, _, _ = classify_pty_alert("You have reached your weekly limit. What do you want to do?")
    assert kill is True


def test_five_hour_limit_is_terminal():
    _, kill, _, _ = classify_pty_alert("... reached your 5-hour limit ...")
    assert kill is True


def test_session_limit_is_terminal_with_reset():
    alert, kill, _, _ = classify_pty_alert("you hit your session limit · resets 3pm\nupgrade your plan")
    assert kill is True
    assert "3pm" in alert


def test_auth_failure_flags_is_auth_and_kills():
    _, kill, is_auth, _ = classify_pty_alert("... API Error: 401 invalid authentication credentials ...")
    assert kill is True
    assert is_auth is True


def test_no_conversation_signals_reset_without_alert():
    alert, kill, is_auth, no_conv = classify_pty_alert("... no conversation found to continue ...")
    assert no_conv is True
    assert alert is None
    assert kill is False


# --- is_fresh gating: an error already dismissed at the prompt is ignored -----

def test_stale_rate_limit_at_prompt_is_ignored():
    alert, _, _, _ = classify_pty_alert("RateLimitError happened earlier\n❯ ")
    assert alert is None


def test_clean_buffer_matches_nothing():
    alert, kill, is_auth, no_conv = classify_pty_alert("just normal output ❯")
    assert alert is None and kill is False and is_auth is False and no_conv is False
