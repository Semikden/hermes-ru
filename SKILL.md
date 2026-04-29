# Hermes Telegram RU

Автоматическая русификация Hermes Agent через LLM.

## Файлы

| Файл | Назначение |
|------|------------|
| `find_en_strings.py` | Находит English user-facing строки |
| `to_translate.txt` | English строки для перевода |
| `translated_batch.txt` | Русские переводы |
| `apply_translations_safe.py` | Применяет переводы к run.py |
| `apply_safe.py` | Резервное применение с бэкапом |
| `ru_update.sh` | Полный цикл одной командой |

## Быстрый старт

```bash
cd /root/hermes-ru
./ru_update.sh
```

Или по шагам:

```bash
# 1. Найти English строки
python3 find_en_strings.py

# 2. Перевести через Grok (если есть ключ)
python3 translate_llm.py

# 3. Применить
python3 apply_translations_safe.py

# 4. Проверить синтаксис
python3 -m py_compile /root/hermes-agent-src/gateway/run.py
```

## Что переводится

✅ Chat-сообщения (Telegram, Discord)
✅ Emoji-префиксы (⚡✅❌⚠️🧠📌)
✅ User-facing ошибки
✅ Команды help

❌ НЕ переводится:
- Terminal/CLI команды
- Config keys
- ENV variables
- Docstrings
- Code

## API Key

Использует xAI Grok или MiniMax через env var `MINIMAX_API_KEY`.

Или MiniMax через `MINIMAX_API_KEY` env var.

## GitHub Sync

```bash
cd /root/hermes-ru
git push
```

## История

- 29.04.2026: 17 новых переводов (всего ~50+)
- Строки найдены через find_en_strings.py
- Переведены через Grok 3 Mini
