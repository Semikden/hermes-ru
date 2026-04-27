---
name: hermes-session-ingest
description: "Автоматический ingest сессий Hermes в Obsidian wiki через LLM. Скрипт ingest-wiki.js читает новые .jsonl сессии, извлекает факты через MiniMax API, пишет в _gera-wiki/, архивирует старые страницы. Используй когда: нужно настроить автоматический semantic memory pipeline, создать cron для извлечения фактов из сессий, или обновить Obsidian wiki из истории разговоров без ручного запуска."
category: devops
tags: [hermes, obsidian, memory, automation, cron]
---

# hermes-session-ingest

Автоматический pipeline для извлечения фактов из сессий Hermes в Obsidian wiki.

## Архитектура

```
~/.hermes/sessions/*.jsonl
    → ingest-wiki.js (Node.js)
    → MiniMax API (или любой OpenAI-compatible)
    →
/root/Obsidian/_gera-wiki/
    ├── entities/Денис.md
    ├── concepts/Решения.md
    ├── concepts/Техника.md
    ├── projects/Прогресс.md
    ├── archive/
    └── index.md
```

## Файл скрипта

Путь: `/root/.hermes/scripts/ingest-wiki.js`

Скрипт:
- Читает `.jsonl` сессии из `~/.hermes/sessions/`
- Пропускает через LLM (MiniMax API) для извлечения структурированных фактов
- Пишет результаты в `/_gera-wiki/` по категориям
- Ведуёт `index.md`
- Архивирует страницы старше 60 дней
- Manifest: `/_gera-wiki/.manifest.json` (last_ingest, ingested_sessions, total_ingested)

## Запуск

```bash
# Тест (dry-run)
node /root/.hermes/scripts/ingest-wiki.js --dry-run

# Реальный ingest
node /root/.hermes/scripts/ingest-wiki.js
```

## Cron

```cron
0 */6 * * * /root/.hermes/scripts/ingest-wiki.js >> /root/.hermes/logs/ingest.log 2>&1
```

(каждые 6 часов)

## Зависимости

- Node.js ≥ 18 (есть: v22.22.2)
- `MINIMAX_API_KEY` в env
- Python 3 (есть: 3.12.3)

## Конфиг скрипта

| Константа | Значение |
|-----------|---------|
| `SESSIONS_DIR` | `~/.hermes/sessions` |
| `WIKI_DIR` | `/root/Obsidian/_gera-wiki` |
| `MANIFEST_PATH` | `_gera-wiki/.manifest.json` |
| `MODEL` | `MiniMax-M2.7` |

## Pitfalls

1. **MiniMax API key** — читается из `process.env.MINIMAX_API_KEY`. Убедись что переменная доступна в cron.
2. **Empty sessions** — пропускаются если < 150 символов conversation.
3. **Skip flag** — если LLM вернул `{"skip": true}`, сессия не пишется.
4. **Rate limit** — 600ms delay между вызовами. Увеличь если 429.
5. **Archive age** — 60 дней. Меняй в `runCompaction()`.

## Проверка после запуска

```bash
ls -la /root/Obsidian/_gera-wiki/entities/
cat /root/Obsidian/_gera-wiki/.manifest.json
tail -20 /root/.hermes/logs/ingest.log
```
