---
name: hermes-ru
description: "Русификация Telegram-интерфейса Hermes Agent. Патчит gateway/run.py — системные сообщения, статусы инструментов, описания скиллов, обработчики команд (/queue, /steer, /model, /reasoning, /fast, /voice, /background, /btw, /approve, /undo, /retry). Включает post-merge git hook для автоматического восстановления патча после git pull. Прогресс: ~90% (run.py), осталось: platform adapters, agent/display.py, tools/."
version: 1.0.0
author: Denis (Hermes community)
---

# Hermes RU — Русификация Telegram-интерфейса

## Что делает этот скилл

Патчит `gateway/run.py` в hermes-agent-src:
- Системные сообщения (шлюз, сессии, ошибки)
- Метки инструментов в Telegram (progress_callback)
- Все user-facing строки на русский

А ТАКЖЕ переводит `description` всех скиллов на русский язык — чтобы команда `/commands` отображалась на русском.

> **CLI-часть (`agent/display.py`)** — там терминал/браузер отображается только в терминале, **не в Telegram**. Этот скилл НЕ трогает agent/display.py для Telegram-интерфейса.

## Совместимость

- Hermes Agent v0.11.0+
- Исходники в `/root/hermes-agent-src/` (editable install)
- **НЕ работает** если hermes-agent установлен только из PyPI (site-packages)

## Как применить

### Шаг 1 — Проверь что исходники на месте

```bash
python3 -c "import hermes.gateway.run as r; print(r.__file__)"
```

Должен показать путь содержащий `hermes-agent-src`. Если видишь `site-packages` — исходники не найдены, сообщи пользователю.

### Шаг 2 — Создай резервную копию

```bash
cp /root/hermes-agent-src/gateway/run.py /root/hermes-agent-src/gateway/run.py.bak
```

### Шаг 3 — Найди progress_callback и добавь словарь переводов

Открой `run.py`, найди функцию `progress_callback` (≈строка 9362). После её объявления добавь словарь `_RU`:

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

> ⚠️ Важно: в словаре `"browser": "браузер"` — **один** ключ, а не отдельные `browser_navigate`, `browser_scroll` и т.д. Все браузерные команды приходят как `browser`.

Затем в f-строках внутри progress_callback замени `{tool_name}` на `{tool_label}`.

### Шаг 4 — Переведи системные сообщения

Используй точный поиск и замену (строки могут отличаться по номеру — ищи по тексту):

| Найди | Замени на |
|-------|-----------|
| `_INTERRUPT_REASON_GATEWAY_SHUTDOWN = "Gateway shutting down"` | `_INTERRUPT_REASON_GATEWAY_SHUTDOWN = "⚠️ Шлюз выключается"` |
| `_INTERRUPT_REASON_GATEWAY_RESTART = "Gateway restarting"` | `_INTERRUPT_REASON_GATEWAY_RESTART = "🔄 Шлюз перезапускается"` |
| `return "restarting" if self._restart_requested else "shutting down"` | `return "перезапускается" if self._restart_requested else "выключается"` |
| `return "shutting down" if self._restart_requested else "shutting down"` (или аналог) | `return "выключается" if self._restart_requested else "выключается"` |
| `"previous session was stopped or interrupted"` | `"предыдущая сессия была остановлена или прервана"` |
| `"Текущая задача будет прервана"` или оригинал | `"Отвечу как только текущая задача завершится."` (уже на русском в v0.11.0) |
| `"⏳ Still working..."` или его русский аналог | найди текущую строку и переведи если на английском |
| фраза с `Session automatically reset` | `f"◐ Сессия сброшена ({reason_text}). История диалога очищена.\n"` |
| фраза с `Conversation history cleared` | уже в составе строки выше |
| фраза с `Use /resume to browse` | `f"Используй /resume чтобы найти и восстановить предыдущую сессию.\n"` |
| `"⚡️ Stopped. You can continue this session."` | найди по ключевым словам `Stopped` и замени на `⚡️ Остановлено. Можешь продолжить эту сессию.` |
| строка с `♻️ Gateway restarted` | `"♻️ Шлюз успешно перезапущен. Сессия продолжается."` |
| строка с `⚡️ YOLO mode ON` | найди и замени на `⚡️ Режим YOLO ВКЛ для этой сессии — все команды выполняются без подтверждения. Осторожно.` |
| строка с `⚡️ YOLO mode OFF` | найди и замени на `⚠️ Режим YOLO ВЫКЛ для этой сессии — опасные команды потребуют подтверждения.` |

### Дополнительные строки (не вошли в основную таблицу — искать по тексту)

| Найди | Замени на |
|-------|-----------|
| `⏳ Queued for the next turn` | `⏳ Поставлено в очередь` |
| `⚡ Interrupting current task` | `⚡ Прерываю текущую задачу` |
| `✗ Failed to send response to update process` | `✗ Не удалось отправить ответ процессу обновления` |
| `✓ Sent \`{label}\` to the update process` | `✓ Отправлено \`{label}\` в процесс обновления` |
| `Usage: /queue <prompt>` | `Использование: /queue <текст>` |
| `Queued for the next turn.` | `Поставлено в очередь на следующий ход.` |
| `Usage: /steer <prompt>` | `Использование: /steer <текст>` |
| `⚠️ Steer failed:` | `⚠️ Steer не удался:` |
| `⏩ Steer queued — arrives after the next tool call` | `⏩ Steer поставлен — придёт после следующего вызова инструмента` |
| `Steer rejected (empty payload).` | `Steer отклонён (пустой запрос).` |
| `⏳ Agent is running — \`/{cmd}\` can't run mid-turn.` | `⏳ Агент работает — \`/{cmd}\` нельзя запустить посреди хода.` |
| `Command \`/{cmd}\` was blocked by a hook.` | `Команда \`/{cmd}\` заблокирована хуком.` |
| `Quick command error:` | `Ошибка быстрой команды:` |
| `Quick command '/{cmd}' has no command defined.` | `Быстрая команда '/{cmd}' не определена.` |
| `Quick command '/{cmd}' has no target defined.` | `Быстрая команда '/{cmd}' не имеет цели.` |
| `Quick command '/{cmd}' has unsupported type` | `Быстрая команда '/{cmd}' имеет неподдерживаемый тип` |
| `Error: {result.error_message}` | `Ошибка: {result.error_message}` |
| `Model switched to \`` | `Модель изменена на \`` |
| `_(session only — use \`/model <name> --global\` to persist)_` | `_(сессия — используй \`/model <name> --global\` чтобы сохранить)_` |
| `Prompt caching: enabled` | `Кэширование промптов: включено` |
| `Warning: {msg}` | `Предупреждение: {msg}` |
| `Saved to config.yaml (\`--global\`)` | `Сохранено в config.yaml (\`--global\`)` |
| `_(session only -- add \`--global\` to persist)_` | `_(сессия — добавь \`--global\` для сохранения)_` |
| `⚠️ Unknown argument: \`{effort}\`` | `⚠️ Неизвестный аргумент: \`{effort}\`` |
| `**Valid levels:**` | `**Допустимые уровни:**` |
| `⚡ /fast is only available for OpenAI models` | `⚡ /fast доступен только для OpenAI-моделей` |
| `⚡ Priority Processing` | `⚡ Приоритетная обработка` |
| `Current mode: \`{status}\`` | `Текущий режим: \`{status}\`` |
| `**Valid options:**` | `**Допустимые варианты:**` |
| `Voice mode enabled.` | `Голосовой режим включён.` |
| `Voice mode disabled. Text-only replies.` | `Голосовой режим выключен. Только текстовые ответы.` |
| `Auto-TTS enabled.` | `Авто-TTS включён.` |
| `Voice mode: Off (text only)` | `Голосовой режим: Выкл (только текст)` |
| `Voice mode: On (voice reply to voice messages)` | `Голосовой режим: Вкл (голосовые ответы на голосовые)` |
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
| `❌ Background task {task_id} failed: {e}` | `❌ Фоновая задача {task_id} не удалась: {e}` |
| `Usage: /btw <question>` | `Использование: /btw <вопрос>` |
| `Answers using session context.` | `Отвечает с использованием контекста сессии.` |
| `Nothing to undo.` | `Нечего отменять.` |
| `↩️ Undid {n} message(s).` | `↩️ Отменено {n} сообщений.` |
| `✅ Command{'s'} approved{scope_msg}. The agent is resuming...` | `✅ Команда одобрена{scope_msg}. Агент продолжает...` |
| `🎤 I received your voice message but can't transcribe it` | `🎤 Получил голосовое сообщение, но не могу распознать` |
| `📖 **Hermes Commands**` | `📖 **Команды Hermes**` |
| `⚡ **Skill Commands**` | `⚡ **Команды скиллов**` |
| `... and {n} more. Use \`/commands\` for the full paginated list.` | `... и ещё {n}. Используй \`/commands\` для полного списка.` |

### Шаг 5 — Перезапусти

```bash
hermes gateway restart
```

> ⚠️ **НИКОГДА** не используй `hermes gateway run --replace` — вызывает мультипроцессорный конфликт и ошибку 401. Только `hermes gateway restart`.

### Шаг 6 — Проверь

Напиши боту в Telegram что-нибудь, убедись что:
- Системные сообщения на русском
- Метки инструментов в прогрессе на русском

### Шаг 7 — Откат (если сломалось)

```bash
cp /root/hermes-agent-src/gateway/run.py.bak /root/hermes-agent-src/gateway/run.py
hermes gateway restart
```

### Шаг 5 — Переведи descriptions всех скиллов

Программно (рекомендуется). Скрипт ниже проходит по всем `SKILL.md` и переводит `description` в YAML frontmatter на русский:

```python
import os, re
TRANSLATIONS = {
    "claude-code": "Делегирование задач Claude Code (CLI-агент Anthropic).",
    "obsidian": "Чтение, поиск и создание заметок в Obsidian vault.",
    "fitness-nutrition": "Планировщик тренировок и трекер питания.",
    # ... все остальные скиллы
}
for root, dirs, files in os.walk("/root/.hermes/skills"):
    for f in files:
        if f != "SKILL.md": continue
        path = os.path.join(root, f)
        skill = os.path.basename(root)
        if skill not in TRANSLATIONS: continue
        with open(path) as fp: c = fp.read()
        c = re.sub(r'^description:.*$', f'description: "{TRANSLATIONS[skill]}"', c, count=1, flags=re.MULTILINE)
        with open(path, "w") as fp: fp.write(c)
```

Полный словарь всех 86 описаний — в памяти агента (секция TRANSLATIONS). Агент-исполнитель должен сам подставить полный словарь.

```
Линия 435: _INTERRUPT_REASON_GATEWAY_SHUTDOWN = "⚠️ Шлюз выключается"
Линия 436: _INTERRUPT_REASON_GATEWAY_RESTART = "🔄 Шлюз перезапускается"
Линия 1151: return "перезапускается" if self._restart_requested else "выключается"
Линия 1573: f"⏳ Поставлено в очередь{status_detail}..." (БЫЛО: "Queued for the next turn")
Линия 1578: f"⚡ Прерываю текущую задачу{status_detail}..." (БЫЛО: "Interrupting current task")
Линия 1646: action = "перезапускается" if self._restart_requested else "выключается"
Линия 3233: f"✗ Не удалось отправить ответ процессу обновления..." (БЫЛО: "Failed to send response...")
Линия 3236: f"✓ Отправлено `{label}` в процесс обновления." (БЫЛО: "Sent to the update process")
Линия 3326: return "⚡️ Остановлено. Можешь продолжить эту сессию."
Линия 3351: "Использование: /queue <текст>" (БЫЛО: "Usage: /queue <prompt>")
Линия 3362: "Поставлено в очередь на следующий ход." (БЫЛО: "Queued for the next turn")
Линия 3372: "Использование: /steer <текст>" (БЫЛО: "Usage: /steer <prompt>")
Линия 3392: f"⚠️ Steer не удался: {exc}" (БЫЛО: "Steer failed")
Линия 3395: f"⏩ Steer поставлен — придёт после следующего вызова инструмента" (БЫЛО: "Steer queued")
Линия 3396: "Steer отклонён (пустой запрос)." (БЫЛО: "Steer rejected")
Линия 3469-3470: "⏳ Агент работает — нельзя запустить посреди хода"
Линия 3597: f"Команда `/{cmd}` заблокирована хуком."
Линия 3753: f"Ошибка быстрой команды: {e}"
Линия 3755: f"Быстрая команда '/{cmd}' не определена."
Линия 3763: f"Быстрая команда '/{cmd}' не имеет цели."
Линия 3768: f"Быстрая команда '/{cmd}' имеет неподдерживаемый тип"
Линия 4118: reason_text = "предыдущая сессия была остановлена или прервана"
Линия 4127: f"◐ Сессия сброшена ({reason_text}). История диалога очищена.\n"
Линия 4128: f"Используй /resume чтобы найти и восстановить предыдущую сессию.\n"
Линия 5235: return "⚡️ Остановлено. Агент ещё не запустился — можешь продолжить сессию."
Линия 5245: return "⚡️ Остановлено. Можешь продолжить эту сессию."
Линия 5554: "Ошибка: {result.error_message}" (модель)
Линия 5598-5599: "Модель изменена на `{model}`", "Провайдер: {plabel}"
Линия 5618: "_(сессия — используй `/model --global`...)_"
Линия 5773: "Кэширование промптов: включено"
Линия 5776: "Предупреждение: {msg}"
Линия 5779: "Сохранено в config.yaml (`--global`)"
Линия 5781: "_(сессия — добавь `--global`...)_"
Линия 5817: "_(вступит в силу со следующего сообщения)_"
Линия 5855: "_(вступит в силу со следующего сообщения)_"
Линия 5876: "Нет предыдущего сообщения для повтора."
Линия 5910: "Нечего отменять." (undo)
Линия 5919: "↩️ Отменено {n} сообщений."
Линия 5943: "Не удалось сохранить домашний канал"
Линия 5946: "✅ Домашний канал установлен: {chat_name}"
Линия 5978-5981: "Голосовой режим включён..."
Линия 5988: "Голосовой режим выключен. Только текстовые ответы."
Линия 5994-5996: "Авто-TTS включён..."
Линия 6005-6007: "Голосовой режим: Выкл..."
Линия 6045: "Голосовые каналы не поддерживаются на этой платформе."
Линия 6049: "Эта команда работает только на Discord-сервере."
Линия 6055: "Сначала подключись к голосовому каналу."
Линия 6072-6073: "Голосовые зависимости не установлены..."
Линия 6085-6086: "Подключился к голосовому каналу..."
Линия 6090: "Не удалось подключиться к голосовому каналу."
Линия 6098/6101: "Не в голосовом канале."
Линия 6113: "Покинул голосовой канал."
Линия 6440-6444: "Использование: /background..."
Линия 6458: "🔄 Фоновая задача запущена:..."
Линия 6547: "✅ Фоновая задача завершена\nPrompt:..."
Линия 6558: "(Ответ не сгенерирован)"
Линия 6595: "❌ Фоновая задача {task_id} не удалась: {e}"
Линия 6605-6608: "Использование: /btw..."
Линия 6617: "Команда /btw уже выполняется..."
Линия 6818-6832: настройки рассуждений (уже переведены)
Линия 6854: "`/reasoning reset --global` не поддерживается"
Линия 6858: "Переопределение рассуждений для сессии сброшено"
Линия 6865: "⚠️ Неизвестный аргумент: `{effort}`"
Линия 6876-6879: рассуждения сохранены / сессия / ошибка
Линия 6897: "⚡ /fast доступен только для OpenAI-моделей"
Линия 6922-6924: "⚡ Приоритетная обработка..."
Линия 6937: "⚠️ Неизвестный аргумент: `{args}`"
Линия 6942-6943: "Приоритетная обработка: {LABEL}..."
Линия 6958: return "⚠️ Режим YOLO ВЫКЛ..."
Линия 6961: return "⚡️ Режим YOLO ВКЛ..."
Линия 6985-6998: обработка verbose (не проверено)
Линия 7595-7605: /approve (не проверено — уже переводится)
Линия 7654: "✅ Команда одобрена. Агент продолжает..."
Линия 7675: "Нет команды ожидающей отклонения."
Линия 7691: "❌ Команда отклонена."
Линия 8162: return "♻️ Шлюз успешно перезапущен. Сессия продолжается."
Линия 9364-9387: _RU = { ... } словарь в progress_callback

### Не проверено / осталось
- `agent/display.py` — прогресс бар, spinner (не Telegram, но влияет на UX)
- `gateway/platforms/telegram.py` — платформенные адаптеры (нотификации, ошибки)
- `hermes_cli/commands.py` — help-тексты команд в CLI (не в Telegram)
- Строки в `run_agent.py` — возможны English в ответах агента (не интерфейсные)
```

## После патча — запушь бэкап

```bash
/root/.hermes/scripts/backup-to-github.sh "feat: русификация Telegram-интерфейса (hermes-ru skill)"
```

---

## 🔁 Автоматическое восстановление патча после git pull (post-merge hook)

Hermes обновляется через `git pull` в `/root/hermes-agent-src/`. После каждого обновления патч **слетает** — нужно переприменять вручную. Автоматизируем через `post-merge` git hook.

### Создание патча

```bash
cd /root/hermes-agent-src
git fetch origin main
git diff origin/main -- gateway/run.py > /root/.hermes/skills/hermes-ru/ru.patch
```

> ⚠️ **НИКОГДА** не используй `git diff gateway/run.py` (без `origin/main`) — это сохранит только незакоммиченные изменения, которые уже потеряны при первом `git stash`.

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

Ожидаемый вывод: `[hermes-ru] ✅ Русификация восстановлена после обновления`

### Пересоздание патча (после изменений)

Если патч перестал применяться — upstream сильно изменился. Пересоздай:

```bash
cd /root/hermes-agent-src
git fetch origin main
git checkout origin/main -- gateway/run.py  # сброс на upstream
git apply --ignore-whitespace /root/.hermes/skills/hermes-ru/ru.patch  # применение нашего патча
# если конфликт — чини вручную, затем:
git diff origin/main -- gateway/run.py > /root/.hermes/skills/hermes-ru/ru.patch
```

### Откат к чистому upstream

```bash
cd /root/hermes-agent-src
git checkout origin/main -- gateway/run.py
rm /root/.hermes/skills/hermes-ru/ru.patch  # удали устаревший патч
```

### Также сохрани патч в backup repo

```bash
mkdir -p /tmp/hermes-gera-backup/skills/hermes-ru
cp /root/.hermes/skills/hermes-ru/ru.patch /tmp/hermes-gera-backup/skills/hermes-ru/ru.patch
cd /tmp/hermes-gera-backup && git add -A && git commit -m "🔧 hermes-ru: обновлённый патч" && git push
```
