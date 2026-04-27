# 🇷🇺 Hermes Telegram RU

> Полная русификация Telegram-интерфейса Hermes Agent.

[![Hermes Agent v0.11+](https://img.shields.io/badge/Hermes%20Agent-v0.11%2B-blue)](https://github.com/nousresearch/hermes-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Возможности

- ✅ **Прогресс-сообщения** — `terminal` → `💻 терминал`, `read_file` → `📖 читаю` и 30+ других
- ✅ **Системные сообщения** — рестарт, сброс сессии, home channel
- ✅ **Busy-состояния** — `Queued for the next turn` → `⏳ В очереди на следующий ход`
- ✅ **Команды** — `/queue`, `/steer`, `/stop`, `/update` и другие
- ✅ **Voice/Gateway/Debug статусы** — всё на русском
- ✅ **Автоматическое восстановление** после `git pull` / обновлений

## 📊 Прогресс перевода

| Категория | Строк | Переведено |
|-----------|-------|------------|
| progress_callback (инструменты) | ~35 | ✅ 100% |
| Системные сообщения | ~15 | ✅ 100% |
| Команды (/queue, /steer, etc) | ~25 | ✅ 100% |
| Voice/Status статусы | ~15 | ✅ 100% |
| Остальное | ~20 | 🔄 В работе |

**Текущий аудит:** 63 непереведённых строк обнаружено в `run.py` — ведётся работа.

## 🚀 Быстрая установка

### Предварительные требования

```bash
# Проверь что исходники на месте
python3 -c "import gateway.run; print(gateway.run.__file__)"
# Должен показать путь содержащий hermes-agent-src
```

### Установка

```bash
# 1. Клонируй репозиторий
git clone https://github.com/Semikden/hermes-ru.git
cd hermes-ru

# 2. Скопируй файлы
cp -r SKILL.md ~/.hermes/skills/hermes-ru/
cp -r audit_ru.py ~/.hermes/skills/hermes-ru/
chmod +x ~/.hermes/skills/hermes-ru/audit_ru.py

# 3. Запусти аудит (опционально)
python3 ~/.hermes/skills/hermes-ru/audit_ru.py

# 4. Примени патч
cd ~/.hermes/hermes-agent  # или путь к исходникам
git apply < /path/to/hermes-ru/ru.patch

# 5. Рестарт
hermes gateway restart
```

## 📁 Структура репозитория

```
hermes-ru/
├── SKILL.md          # Основной скилл — все патчи и инструкции
├── ru.patch          # Патч для apply (если нет SKILL.md)
├── audit_ru.py       # Аудит-скрипт — найти непереведённые строки
└── README.md         # Этот файл
```

## 🔍 Аудит — как работает

```bash
python3 ~/.hermes/skills/hermes-ru/audit_ru.py
```

Скрипт анализирует `gateway/run.py` и находит все English строки, которые отправляются в чат (Telegram и другие платформы). **Не затрагивает CLI-логи**.

### Как добавить новый перевод

1. Запусти `audit_ru.py`
2. Найди нужную строку
3. Добавь её в `_RU` словарь (для progress_callback) или патчни напрямую
4. Проверь что не добавляешь эмодзи в `_RU` — `get_tool_emoji()` уже добавляет их

## ⚠️ После обновления Hermes Agent

Если после `git pull` или обновления русский язык сбросился:

```bash
cd ~/.hermes/hermes-agent  # путь к hermes-agent-src
git apply < ~/.hermes/skills/hermes-ru/ru.patch
hermes gateway restart
```

## 🔧 Патч вручную (без git)

Если патч не применяется:

```bash
# Найди строку
grep -n "English text" ~/.hermes/hermes-agent/gateway/run.py

# Патчни через sed
sed -i 's/"English text"/"Русский текст"/g' ~/.hermes/hermes-agent/gateway/run.py

# Или через Python
python3 -c "
import re
f = '~/.hermes/hermes-agent/gateway/run.py'
c = open(f).read()
c = c.replace('English text', 'Русский текст')
open(f, 'w').write(c)
"
```

## 📝 Текущий перевод (progress_callback)

| English | Русский |
|---------|---------|
| terminal | терминал |
| read_file | читаю |
| write_file | пишу |
| patch | патчу |
| search_files | ищу |
| browser | браузер |
| browser_navigate | открываю |
| browser_click | кликаю |
| browser_scroll | прокручиваю |
| vision_analyze | анализирую |
| execute_code | код |
| delegate_task | делегирую |
| session_search | поиск сессий |
| send_message | отправляю |
| cronjob | крон |
| memory | память |

## 🤝 Вклад

Форки приветствуются! Если нашёл непереведённую строку:

1. Запусти `audit_ru.py`
2. Добавь перевод
3. Отправь PR

## 📜 Лицензия

MIT — используй свободно.

---

**Автор:** Denis (Денис)
**Hermes Agent:** [nousresearch/hermes-agent](https://github.com/nousresearch/hermes-agent)
