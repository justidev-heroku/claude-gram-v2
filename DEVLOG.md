# DEVLOG

## 2026-07-23 — Лимит сессии: кнопки вместо перезапуска

При достижении лимита сессии Claude бот больше НЕ перезапускается. Теперь
приходит алерт с двумя инлайн-кнопками:

- «✅ Понял» (`limit:ack`) — просто снимает клавиатуру.
- «▶️ Продолжить работу» (`limit:resume`) — шлёт Claude промпт
  «Continue from where you left off.» после сброса лимита.

Что изменилось:

- `classify_pty_alert` в `install.py` теперь возвращает 5 значений — добавлен
  `session_limit_reset` (строка времени сброса или `""` для живого баннера,
  иначе `None`). `kill_after_alert = False` для лимита сессии.
- Живым баннером лимита считается буфер, где ОДНОВРЕМЕННО есть
  `hit your session limit`, `resets` и один из `/upgrade` / `usage-credits`
  / `/usage` (плюс прежняя проверка `is_fresh`). Это отсекает ложное
  срабатывание от эхо агент-ошибки
  «Agent terminated early due to an API error: You've hit your session limit».
- Время сброса парсится узким regex
  `resets\s+(\d{1,2}:\d{2}\s*[ap]m(?:\s*\([^)]*\))?)` — без жадности,
  `/upgrade` в строку не попадает.
- В `main()` добавлен дедуп по сигнатуре сброса (файл
  `~/.claude/channels/telegram/last_session_limit`): повторный тот же баннер
  не пересылается.
- В `server.py` добавлены колбэки `limit:ack` и `limit:resume`.
- Тесты `tests/test_alert_classification.py` и `tests/test_limit_matching.py`
  обновлены под новую арность и новые кейсы.

Не трогалось: billing / weekly / 5-hour / auth(401) / rate-limit / overloaded,
форк-сессии, ветка «no conversation found», прочие колбэки.
