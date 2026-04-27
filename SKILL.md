---
name: hermes-ru
description: "Русификация Telegram-интерфейса Hermes Agent. Патчит gateway/run.py — системные сообщения, статусы инструментов (browser sub-tools включены), описания скиллов, обработчики команд. GitHub repo: Semikden/hermes-ru. Прогресс: ~95%."
version: 1.1.0
author: Denis (Hermes community)
---

# Hermes RU — Русификация Telegram-интерфейса

## Что делает этот скилл

Патчит `gateway/run.py` в hermes-agent-src:
- Системные сообщения (шлюз, сессии, ошибки)
- Метки инструментов в Telegram (progress_callback) — ВСЕ browser sub-tools включены
- Все user-facing строки на русский

А ТАКЖЕ переводит `description` всех скиллов на русский язык.

## Совместимость

- Hermes Agent v0.11.0+
- Исходники в `/root/hermes-agent-src/` (editable install)
- **НЕ работает** если hermes-agent установлен только из PyPI (site-packages)

## Как применить

### Шаг 1 — Проверь что исходники на месте

```bash
python3 -c "import hermes.gateway.run as r; print(r.__file__)"
```

Должен показать путь содержащий `hermes-agent-src`.

### Шаг 2 — Создай резервную копию

```bash
cp /root/hermes-agent-src/gateway/run.py /root/hermes-agent-src/gateway/run.py.bak
```

### Шаг 3 — Найди progress_callback и обнови словарь _RU

Открой `run.py`, найди функцию `progress_callback` (≈строка 9362). Замени словарь `_RU` на:

```python
_RU = {
    "terminal": "терминал",
    "process": "процесс",
    "read_file": "читаю файл",
    "write_file": "пишу файл",
    "patch": "патчу файл",
    "search_files": "ищу в файлах",
    "web_search": "ищу в сети",
    "web_extract": "читаю страницу",
    "browser": "браузер",
    "browser_navigate": "открываю страницу",
    "browser_snapshot": "снимок страницы",
    "browser_click": "кликаю",
    "browser_type": "ввожу текст",
    "browser_scroll": "прокручиваю",
    "browser_back": "назад",
    "browser_press": "нажимаю",
    "browser_get_images": "ищу картинки",
    "browser_vision": "анализирую страницу",
    "browser_console": "консоль браузера",
    "browser_dialog": "диалог браузера",
    "browser_cdp": "браузер CDP",
    "vision_analyze": "смотрю картинку",
    "image_generate": "генерирую изображение",
    "text_to_speech": "озвучиваю",
    "session_search": "поиск сессий",
    "memory": "обновляю память",
    "todo": "планирую",
    "clarify": "уточняю",
    "execute_code": "выполняю код",
    "delegate_task": "делегирую задачу",
    "cronjob": "планировщик",
    "send_message": "отправляю сообщение",
    "skill_view": "читаю скилл",
    "skill_manager": "управляю скиллами",
}
tool_label = _RU.get(tool_name, tool_name) if tool_name else tool_name
```

### Шаг 4 — Переведи системные сообщения

| Найди | Замени на |
|-------|-----------|
| `_INTERRUPT_REASON_GATEWAY_SHUTDOWN = "Gateway shutting down"` | `_INTERRUPT_REASON_GATEWAY_SHUTDOWN = "⚠️ Шлюз выключается"` |
| `_INTERRUPT_REASON_GATEWAY_RESTART = "Gateway restarting"` | `_INTERRUPT_REASON_GATEWAY_RESTART = "🔄 Шлюз перезапускается"` |
| `return "restarting" if self._restart_requested else "shutting down"` | `return "перезапускается" if self._restart_requested else "выключается"` |
| `"previous session was stopped or interrupted"` | `"предыдущая сессия была остановлена или прервана"` |
| фраза с `Session automatically reset` | `f"◐ Сессия сброшена ({reason_text}). История диалога очищена.\n"` |
| фраза с `Use /resume to browse` | `f"Используй /resume чтобы найти и восстановить предыдущую сессию.\n"` |
| строка с `♻️ Gateway restarted` | `"♻️ Шлюз успешно перезапущен. Сессия продолжается."` |
| `⏳ Queued for the next turn` | `⏳ Поставлено в очередь` |
| `⚡ Interrupting current task` | `⚡ Прерываю текущую задачу` |
| `✗ Failed to send response to update process` | `✗ Не удалось отправить ответ процессу обновления` |
| `✓ Sent \`{label}\` to the update process` | `✓ Отправлено \`{label}\` в процесс обновления` |
| `Usage: /queue <prompt>` | `Использование: /queue <текст>` |
| `Usage: /steer <prompt>` | `Использование: /steer <текст>` |
| `⏳ Agent is running — \`/{command}\` can't run mid-turn...` | `⏳ Агент работает — \`/{command}\` нельзя запустить посреди хода.` |
| `Command \`/{command}\` was blocked by a hook.` | `Команда \`/{command}\` заблокирована хуком.` |
| `Error: {result.error_message}` | `Ошибка: {result.error_message}` |
| `Model switched to \`` | `Модель изменена на \`` |
| `Prompt caching: enabled` | `Кэширование промптов: включено` |
| `Warning: {msg}` | `Предупреждение: {msg}` |
| `⚠️ Unknown argument: \`{effort}\`` | `⚠️ Неизвестный аргумент: \`{effort}\`` |
| `**Valid levels:**` | `**Допустимые уровни:**` |
| `⚡ /fast is only available for OpenAI models` | `⚡ /fast доступен только для OpenAI-моделей` |
| `⚡ Priority Processing` | `⚡ Приоритетная обработка` |
| `Current mode: \`{status}\`` | `Текущий режим: \`{status}\`` |
| `**Valid options:**` | `**Допустимые варианты:**` |
| `Voice mode enabled.` | `Голосовой режим включён.` |
| `Voice mode disabled. Text-only replies.` | `Голосовой режим выключен. Только текстовые ответы.` |
| `Auto-TTS enabled.` | `Авто-TTS включён.` |
| `Voice channels are not supported on this platform.` | `Голосовые каналы не поддерживаются на этой платформе.` |
| `This command only works in a Discord server.` | `Эта команда работает только на Discord-сервере.` |
| `You need to be in a voice channel first.` | `Сначала подключись к голосовому каналу.` |
| `Joined voice channel` | `Подключился к голосовому каналу` |
| `Failed to join voice channel. Check bot permissions` | `Не удалось подключиться к голосовому каналу. Проверь права бота` |
| `Not in a voice channel.` | `Не в голосовом канале.` |
| `Left voice channel.` | `Покинул голосовой канал.` |
| `Usage: /background <prompt>` | `Использование: /background <текст>` |
| `🔄 Background task started:` | `🔄 Фоновая задача запущена:` |
| `✅ Background task complete` | `✅ Фоновая задача завершена` |
| `(No response generated)` | `(Ответ не сгенерирован)` |
| `Usage: /btw <question>` | `Использование: /btw <вопрос>` |
| `Nothing to undo.` | `Нечего отменять.` |
| `↩️ Undid {removed_count} message(s).` | `↩️ Отменено {removed_count} сообщений.` |
| `✅ Command{'s'} approved{scope_msg}.` | `✅ Команда{'ы' if count > 1 else ''} одобрена{scope_msg}. Агент продолжает...` |
| `🎤 I received your voice message but can't transcribe it` | `🎤 Получил голосовое сообщение, но не могу распознать` |
| `📖 **Hermes Commands**` | `📖 **Команды Hermes**` |
| `⚡ **Skill Commands**` | `⚡ **Команды скиллов**` |
| `📚 **Commands** ({len(entries)} total, page {page}/{total_pages})` | `📚 **Команды** ({len(entries)} всего, страница {page}/{total_pages})` |

### Шаг 5 — Перезапусти

```bash
hermes gateway restart
```

> ⚠️ **НИКОГДА** не используй `hermes gateway run --replace` — вызывает мультипроцессорный конфликт и ошибку 401. Только `hermes gateway restart`.

### Шаг 6 — Проверь

Напиши боту в Telegram что-нибудь, убедись что браузерные команды показываются на русском.

### Шаг 7 — Откат (если сломалось)

```bash
cp /root/hermes-agent-src/gateway/run.py.bak /root/hermes-agent-src/gateway/run.py
hermes gateway restart
```

---

## Push в GitHub

```bash
cd /root/.hermes/skills/hermes-ru
git add . && git commit -m "feat: browser sub-tools переведены, v1.1"
git push
```

**Токен GitHub** — ищи в скилле `hermes-backup-github`.

---

## 🔁 Автоматическое восстановление патча после git pull

### Создание патча

```bash
cd /root/hermes-agent-src
git fetch origin main
git diff origin/main -- gateway/run.py > /root/.hermes/skills/hermes-ru/ru.patch
```

### Создание hook

```bash
cat > /root/hermes-agent-src/.git/hooks/post-merge << 'EOF'
#!/bin/bash
PATCH="/root/.hermes/skills/hermes-ru/ru.patch"
TARGET="/root/hermes-agent-src/gateway/run.py"
if [ -f "$PATCH" ]; then
  cd /root/hermes-agent-src
  git apply --ignore-whitespace "$PATCH" 2>/dev/null
  if grep -q "Шлюз выключается" "$TARGET" 2>/dev/null; then
    echo "[hermes-ru] ✅ Русификация восстановлена после обновления"
    nohup hermes gateway restart > /dev/null 2>&1 &
  else
    echo "[hermes-ru] ⚠️ Патч не применился — запусти /hermes-ru вручную"
  fi
fi
EOF
chmod +x /root/hermes-agent-src/.git/hooks/post-merge
```

### Тест hook

```bash
bash /root/hermes-agent-src/.git/hooks/post-merge
```

### Также сохрани патч в backup repo

```bash
mkdir -p /tmp/hermes-gera-backup/skills/hermes-ru
cp /root/.hermes/skills/hermes-ru/ru.patch /tmp/hermes-gera-backup/skills/hermes-ru/ru.patch
cd /tmp/hermes-gera-backup && git add -A && git commit -m "🔧 hermes-ru: обновлённый патч" && git push
```
