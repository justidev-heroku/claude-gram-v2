import pytest

def match_limit_alert(pty_buffer: str) -> str | None:
    lower_buf = pty_buffer.lower()
    
    if "ratelimiterror" in lower_buf or "rate limit reached" in lower_buf or "rate limit exceeded" in lower_buf:
        return "⚠️ <b>Claude Code: Превышен лимит запросов (Rate Limit).</b> Пожалуйста, подождите."
    elif "overloadederror" in lower_buf or ("overloaded" in lower_buf and "error" in lower_buf):
        return "⚠️ <b>Claude Code: Серверы Anthropic перегружены (Overloaded).</b> Пожалуйста, повторите попытку."
    elif "billing limit" in lower_buf:
        return "⚠️ <b>Claude Code: Достигнут лимит оплаты (Billing Limit).</b>"
    elif "credit balance too low" in lower_buf or "insufficient credit" in lower_buf or "insufficient funds" in lower_buf:
        return "⚠️ <b>Claude Code: Недостаточно средств на балансе API.</b>"
    elif ("reached your weekly limit" in lower_buf or "weekly limit reached" in lower_buf or "weekly budget exceeded" in lower_buf or
          (("weekly limit" in lower_buf or "weekly budget" in lower_buf) and
           ("what do you want to do" in lower_buf or "upgrade your plan" in lower_buf or "stop and wait" in lower_buf))) and not (
          ("plan's weekly usage limit" in lower_buf or "weekly usage limit on" in lower_buf) and not ("what do you want to do" in lower_buf or "upgrade your plan" in lower_buf)):
        return "⚠️ <b>Claude Code: Достигнут недельный лимит использования.</b>"
    elif ("reached your 5-hour limit" in lower_buf or "5-hour limit reached" in lower_buf or "5-hour budget exceeded" in lower_buf or
          (("5-hour limit" in lower_buf or "5-hour budget" in lower_buf or "5-hour window" in lower_buf) and
           ("what do you want to do" in lower_buf or "upgrade your plan" in lower_buf or "stop and wait" in lower_buf))) and not (
          ("plan's 5-hour usage limit" in lower_buf or "5-hour usage limit on" in lower_buf) and not ("what do you want to do" in lower_buf or "upgrade your plan" in lower_buf)):
        return "⚠️ <b>Claude Code: Достигнут 5-часовой лимит использования. Пожалуйста, подождите сброса лимита.</b>"
    return None


def test_fable5_promotional_banner_does_not_trigger_weekly_limit():
    banner = "Until July 7, you can use up to 50% of your plan's weekly usage limit on Fable 5."
    assert match_limit_alert(banner) is None


def test_actual_weekly_limit_reached_triggers_alert():
    buffer = "You have reached your weekly limit. What do you want to do? 1. Upgrade your plan 2. Stop and wait"
    alert = match_limit_alert(buffer)
    assert alert == "⚠️ <b>Claude Code: Достигнут недельный лимит использования.</b>"


def test_actual_5hour_limit_reached_triggers_alert():
    buffer = "You have reached your 5-hour limit. What do you want to do? 1. Upgrade your plan 2. Stop and wait"
    alert = match_limit_alert(buffer)
    assert alert == "⚠️ <b>Claude Code: Достигнут 5-часовой лимит использования. Пожалуйста, подождите сброса лимита.</b>"
