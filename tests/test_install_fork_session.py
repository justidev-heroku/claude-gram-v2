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


def _load_resume_hint_re():
    src = INSTALL_PY.read_text("utf-8")
    m = re.search(r"resume_hint_re = re\.compile\(\s*(r'.*?')\s*\)", src, re.S)
    assert m, "resume_hint_re not found in install.py wrapper_code"
    return eval(f"re.compile({m.group(1)})")


def _load_build_session_args():
    src = INSTALL_PY.read_text("utf-8")
    fork = re.search(r"def should_fork_session\(.*?\n\n", src, re.S)
    build = re.search(r"(def build_session_args\(.*?)\n\ndef classify_pty_alert", src, re.S)
    assert fork and build, "build_session_args not found in install.py wrapper_code"
    ns = {}
    exec(fork.group(0), ns)          # dependency
    exec(build.group(1), ns)
    return ns["build_session_args"]


should_fork_session = _load_should_fork_session()
resume_hint_re = _load_resume_hint_re()
build_session_args = _load_build_session_args()

NEW_UUID = "11111111-2222-3333-4444-555555555555"
ACTIVE = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_build_no_active_session_starts_fresh():
    args, persist, fork = build_session_args("", "claude-sonnet-5", "claude-sonnet-5", NEW_UUID)
    assert args == ["--session-id", NEW_UUID]
    assert persist == NEW_UUID  # new id must be written to disk
    assert fork is False


def test_build_active_same_model_resumes_without_rewrite():
    args, persist, fork = build_session_args(ACTIVE, "claude-sonnet-5", "claude-sonnet-5", NEW_UUID)
    assert args == ["--resume", ACTIVE]
    assert persist == ""  # file already holds ACTIVE
    assert fork is False


def test_build_active_model_changed_forks():
    args, persist, fork = build_session_args(ACTIVE, "claude-opus-4-8", "claude-sonnet-5", NEW_UUID)
    assert args == ["--resume", ACTIVE, "--fork-session"]
    assert persist == ""  # minted id captured from resume hint
    assert fork is True


def test_build_active_no_last_model_does_not_fork():
    args, _, fork = build_session_args(ACTIVE, "claude-opus-4-8", "", NEW_UUID)
    assert args == ["--resume", ACTIVE]
    assert fork is False


def test_no_fork_when_model_unchanged():
    assert should_fork_session("claude-sonnet-5", "claude-sonnet-5") is False


def test_fork_when_model_changed():
    assert should_fork_session("claude-opus-4-8", "claude-sonnet-5") is True


def test_no_fork_on_first_launch_no_last_model():
    assert should_fork_session("claude-sonnet-5", "") is False


def test_no_fork_when_model_val_missing():
    assert should_fork_session(None, "claude-sonnet-5") is False
    assert should_fork_session("", "claude-sonnet-5") is False


def test_resume_hint_matches_valid_uuid():
    m = resume_hint_re.search(
        "Resume this session with:\nclaude --resume d52b08a6-183c-438c-8fae-b5844d0d17a9\n"
    )
    assert m
    assert m.group(1) == "d52b08a6-183c-438c-8fae-b5844d0d17a9"


def test_resume_hint_matches_when_split_across_reads_via_accumulated_buffer():
    # Simulates os.read() splitting the hint line across two PTY reads:
    # the regex must be matched against the accumulated buffer, not a
    # single chunk, or the id is never captured.
    chunk1 = "Resume this session with:\nclaude --resume d52b08a6-183c-"
    chunk2 = "438c-8fae-b5844d0d17a9\n"
    assert resume_hint_re.search(chunk1) is None
    buffer = chunk1 + chunk2
    m = resume_hint_re.search(buffer)
    assert m and m.group(1) == "d52b08a6-183c-438c-8fae-b5844d0d17a9"


def test_resume_hint_rejects_malformed_uuid():
    assert resume_hint_re.search("claude --resume not-a-real-uuid-but-36-characters-long") is None
