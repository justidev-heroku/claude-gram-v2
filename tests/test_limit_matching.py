import pytest

def match_limit_alert(pty_buffer: str) -> str | None:
    lower_buf = pty_buffer.lower()

    def is_fresh(kws: list) -> bool:
        max_idx = -1
        for kw in kws:
            idx = lower_buf.rfind(kw.lower())
            if idx > max_idx:
                max_idx = idx
        if max_idx == -1:
            return False
        suffix = pty_buffer[max_idx:]
        return "❯" not in suffix and "\u276f" not in suffix
    
    if (any(k in lower_buf for k in ["ratelimiterror", "rate limit reached", "rate limit exceeded"]) and 
            is_fresh(["ratelimiterror", "rate limit reached", "rate limit exceeded"])):
        return "⚠️ <b>Claude Code: Превышен лимит запросов (Rate Limit).</b> Пожалуйста, подождите."
    elif (("overloadederror" in lower_buf or ("overloaded" in lower_buf and "error" in lower_buf)) and 
          is_fresh(["overloadederror", "overloaded"])):
        return "⚠️ <b>Claude Code: Серверы Anthropic перегружены (Overloaded).</b> Пожалуйста, повторите попытку."
    elif "billing limit" in lower_buf and is_fresh(["billing limit"]):
        return "⚠️ <b>Claude Code: Достигнут лимит оплаты (Billing Limit).</b>"
    elif (any(k in lower_buf for k in ["credit balance too low", "insufficient credit", "insufficient funds"]) and 
          is_fresh(["credit balance too low", "insufficient credit", "insufficient funds"])):
        return "⚠️ <b>Claude Code: Недостаточно средств на балансе API.</b>"
    elif (("reached your weekly limit" in lower_buf or "weekly limit reached" in lower_buf or "weekly budget exceeded" in lower_buf or
          (("weekly limit" in lower_buf or "weekly budget" in lower_buf) and
           ("what do you want to do" in lower_buf or "upgrade your plan" in lower_buf or "stop and wait" in lower_buf))) and not (
          ("plan's weekly usage limit" in lower_buf or "weekly usage limit on" in lower_buf) and not ("what do you want to do" in lower_buf or "upgrade your plan" in lower_buf))
          and is_fresh(["reached your weekly limit", "weekly limit reached", "weekly budget exceeded", "weekly limit", "weekly budget"])):
        return "⚠️ <b>Claude Code: Достигнут недельный лимит использования.</b>"
    elif (("reached your 5-hour limit" in lower_buf or "5-hour limit reached" in lower_buf or "5-hour budget exceeded" in lower_buf or
          (("5-hour limit" in lower_buf or "5-hour budget" in lower_buf or "5-hour window" in lower_buf) and
           ("what do you want to do" in lower_buf or "upgrade your plan" in lower_buf or "stop and wait" in lower_buf))) and not (
          ("plan's 5-hour usage limit" in lower_buf or "5-hour usage limit on" in lower_buf) and not ("what do you want to do" in lower_buf or "upgrade your plan" in lower_buf))
          and is_fresh(["reached your 5-hour limit", "5-hour limit reached", "5-hour budget exceeded", "5-hour limit", "5-hour budget", "5-hour window"])):
        return "⚠️ <b>Claude Code: Достигнут 5-часовой лимит использования. Пожалуйста, подождите сброса лимита.</b>"
    elif (("hit your session limit" in lower_buf or ("session limit" in lower_buf and "resets" in lower_buf)) and 
          is_fresh(["hit your session limit", "session limit"])):
        import re
        reset_time = ""
        m = re.search(r"resets\s+([^\n·•]+)", pty_buffer, re.IGNORECASE)
        if m:
            reset_time = f" Сброс: <b>{m.group(1).strip()}</b>."
        return f"⏳ <b>Claude Code: Достигнут лимит сессии.</b>{reset_time} Бот перезапустится автоматически."
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


def test_historical_session_limit_with_prompt_ignored():
    buffer = "You have hit your session limit. It resets at 5:10pm (Europe/Moscow).\nSome other output\n❯ Try 'write a test'"
    assert match_limit_alert(buffer) is None


def test_actual_session_limit_without_prompt_triggers_alert():
    buffer = "You have hit your session limit. It resets at 5:10pm (Europe/Moscow).\nupgrade your plan or wait."
    alert = match_limit_alert(buffer)
    assert alert is not None
    assert "Достигнут лимит сессии" in alert
