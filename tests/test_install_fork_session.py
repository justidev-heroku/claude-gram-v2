"""Tests for should_fork_session() embedded in install.py's wrapper_code template.

The function lives inside a triple-quoted string (it's written out verbatim
to /usr/local/bin/claude-telegram-bot), so we extract and exec just that
function body rather than duplicating the logic here.
"""
import re
from pathlib import Path

INSTALL_PY = Path(__file__).resolve().parent.parent / "install.py"


def _load_should_fork_session():
    src = INSTALL_PY.read_text("utf-8")
    m = re.search(r"def should_fork_session\(.*?\n\n", src, re.S)
    assert m, "should_fork_session not found in install.py wrapper_code"
    ns = {}
    exec(m.group(0), ns)
    return ns["should_fork_session"]


should_fork_session = _load_should_fork_session()


def test_no_fork_when_model_unchanged():
    assert should_fork_session("claude-sonnet-5", "claude-sonnet-5") is False


def test_fork_when_model_changed():
    assert should_fork_session("claude-opus-4-8", "claude-sonnet-5") is True


def test_no_fork_on_first_launch_no_last_model():
    assert should_fork_session("claude-sonnet-5", "") is False


def test_no_fork_when_model_val_missing():
    assert should_fork_session(None, "claude-sonnet-5") is False
    assert should_fork_session("", "claude-sonnet-5") is False
