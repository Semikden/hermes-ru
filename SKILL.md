---
name: hermes-ru
description: "Автоматизированная русификация Telegram-интерфейса Hermes Agent. Патчит run.py (100%, 82/82) + commands.py (~60 описаний команд). GitHub: Semikden/hermes-ru."
version: 2.2
author: Denis (Hermes community)
---

# Hermes RU — Автоматизированная русификация Telegram

## Быстрый старт

```bash
cd /root/hermes-ru
python3 translate_batch.py    # LLM-translate всех строк → translations.txt
python3 apply_translations.py  # Применить переводы к run.py
```

## Что делает

Патчит `gateway/run.py` в hermes-agent-src:
- Системные сообщения (шлюз, сессии, ошибки)
- Метки инструментов в Telegram (progress_callback)
- Все user-facing строки на русский

## Структура репозитория

```
hermes-ru/
├── SKILL.md              ← этот файл
├── ru.patch               ← патч для apply после git pull
├── audit_ru.py            ← аудит непереведённых строк
├── translate_batch.py    ← LLM batch translation (1 запрос на все строки!)
├── apply_translations.py ← применение переводов к run.py
├── translations.txt       ← результат LLM-перевода (82 записи)
└── README.md              ← документация
```

## Workflow — полный цикл

### 1. Аудит (что осталось перевести)

```bash
python3 /root/hermes-ru/audit_ru.py
```

Показывает все непереведённые user-facing строки с номерами строк.

### 2. Batch translation (один LLM-запрос)

```bash
cd /root/hermes-ru
python3 translate_batch.py
```

Результат: `translations.txt` с переводами всех найденных строк.

**Пропускает:**
- Internal-only строки (`logger.`, `__dedup__`, `self._running_agents`)
- Строки с переменными `{result.error_message}`, `{command}`, etc.
- Уже русские строки

### 3. Применение переводов

```bash
cd /root/hermes-ru
python3 apply_translations.py
```

- Создаёт бекап `run.py.ru_backup`
- Применяет переводы из `translations.txt`
- Пропускает строки с переменными (нужна ручная обработка)

### 4. Проверка

```bash
python3 -m py_compile /root/hermes-agent-src/gateway/run.py
python3 /root/hermes-ru/audit_ru.py
```

### 5. Рестарт

```bash
hermes gateway restart
```

### 6. Коммит и пуш

```bash
cd /root/hermes-ru
git add -A && git commit -m "🎉 batch: N переводов"
git push
```

## Обработка строк с переменными

Строки типа `↩️ Undid {removed_count} message(s).\nRemoved: "{preview}"` — **НЕ переводятся автоматически** потому что `{ }` placeholder'ы нельзя безопасно заменить.

Для них — ручной патч через `patch()`:

```python
patch(
    mode="replace",
    path="/root/hermes-agent-src/gateway/run.py",
    old_string='return f"↩️ Undid {removed_count} message(s).\nRemoved: \\"{preview}\\""',
    new_string='return f"↩️ Отменено {removed_count} сообщение(й).\nУдалено: \\"{preview}\\""'
)
```

Список строк с переменными (26 шт) — см. `audit_ru.py` вывод.

## ⚠️ После git pull — восстановление

```bash
cd /root/hermes-agent-src
git pull
cd /root/hermes-ru && python3 apply_translations.py
hermes gateway restart
```

Или через hook (опционально):

```bash
cat > /root/hermes-agent-src/.git/hooks/post-merge << 'EOF'
#!/bin/bash
PATCH="/root/hermes-ru/ru.patch"
TARGET="/root/hermes-agent-src/gateway/run.py"
if [ -f "$PATCH" ]; then
  cd /root/hermes-agent-src
  git apply --ignore-whitespace "$PATCH" 2>/dev/null
  if grep -q "Остановлено" "$TARGET" 2>/dev/null; then
    echo "[hermes-ru] ✅ Русификация восстановлена"
  fi
fi
EOF
chmod +x /root/hermes-agent-src/.git/hooks/post-merge
```

## Регенерация патча

После изменений — обнови ru.patch:

```bash
cd /root/hermes-agent-src
git diff -- gateway/run.py > /root/hermes-ru/ru.patch
```

---

*Обновлено 27.04.2026 — v2.0 (automated batch translation workflow)*
