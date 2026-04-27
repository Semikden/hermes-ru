#!/usr/bin/env python3
"""
Hermes Telegram RU — Audit Script v2
Находит ТОЛЬКО user-facing English строки в gateway/run.py.
Игнорирует: internal return values, logger calls, config values.

Использование:
    python3 audit_ru.py
"""

import re
from pathlib import Path

RUN_PY = Path.home() / ".hermes" / "hermes-agent" / "gateway" / "run.py"
ALT_PATHS = [
    Path("/root/hermes-agent-src/gateway/run.py"),
    Path.home() / "hermes-agent-src" / "gateway" / "run.py",
]

INTERNAL_PATTERNS = [
    r'return\s+"?(restart|shutdown|priority|queue|ignore|pair)',
    r'return\s+f?"(restart|shutdown|priority|queue|ignore|pair)',
    r'logger\.',
    r'__dedup__',
    r'_quick_key',
    r'_pending_messages\[',
    r'\.title\(\)',
    r'platform_env_map',
    r'service_tier',
    r'allowlist',
    r'env_key',
    r'Platform\.',
    r'os\.getenv',
]

INTERNAL_KEYWORDS = [
    "restart", "shutdown", "priority", "queue", "ignore", "pair",
    "_quick_key", "_pending_messages", "platform_env_map", "allowlist",
    "service_tier", "raw.lower()", "raw.strip()"
]


def is_internal(line_num: int, text: str, line: str) -> bool:
    """Определяет internal это строка или user-facing."""

    # Пропускаем явно internal паттерны
    for pattern in INTERNAL_PATTERNS:
        if re.search(pattern, line):
            return True

    # Пропускаем если это return в internal функции
    if 'return "' in line and ('_action_label' in line or '_action_gerund' in line):
        return True

    # Пропускаем очень короткие возвраты
    if re.match(r'^\s*return "[a-z_]+"$', line.strip()):
        return True

    # Пропускаем logger calls
    if 'logger.' in line:
        return True

    # Пропускаем tuple (queue internal message type)
    if '__dedup__' in text:
        return True

    return False


def get_user_facing_strings(filepath: Path) -> list:
    """Находит user-facing строки."""
    content = filepath.read_text()
    lines = content.split('\n')

    results = []

    for i, line in enumerate(lines, 1):
        if re.match(r'^\s*#', line):
            continue

        # Только строки с adapter.send, progress_queue.put( когда это строка
        is_chat_context = ('adapter.send' in line or
                          'progress_queue.put' in line or
                          'return f"' in line or
                          'return "' in line)

        if not is_chat_context:
            continue

        # Извлекаем строки в кавычках
        strings = re.findall(r'"([^"]+)"', line)
        for s in strings:
            s_stripped = s.strip()
            if not s_stripped:
                continue

            # Уже русский?
            if any('\u0400' <= c <= '\u04FF' for c in s_stripped):
                continue

            # Содержит переменные { }
            if '{' in s_stripped and '}' in s_stripped:
                # Это может быть user-facing если содержит понятные слова
                # Пропускаем чисто technical
                if any(kw in s_stripped.lower() for kw in ['chat_id', 'platform', 'session', 'error', 'message', 'command']):
                    pass  # Может быть user-facing
                else:
                    continue

            # Слишком короткие
            if len(s_stripped) < 3:
                continue

            # Проверяем internal
            if is_internal(i, s_stripped, line):
                continue

            results.append((i, s_stripped, line.strip()[:80]))

    # Дедупликация
    seen = set()
    unique = []
    for line_num, text, context in results:
        key = (line_num, text)
        if key not in seen:
            seen.add(key)
            unique.append((line_num, text, context))

    return sorted(unique, key=lambda x: x[0])


def main():
    filepath = RUN_PY if RUN_PY.exists() else None
    if not filepath:
        for p in ALT_PATHS:
            if p.exists():
                filepath = p
                break

    if not filepath:
        print("❌ run.py не найден!")
        sys.exit(1)

    print(f"🔍 Аудит: {filepath}\n")

    results = get_user_facing_strings(filepath)

    if not results:
        print("✅ Все user-facing строки переведены!")
        return

    print(f"❌ Найдено {len(results)} непереведённых user-facing строк:\n")
    print(f"{'Строка':<8} {'Текст':<55} {'Контекст'}")
    print("-" * 90)

    for line_num, text, context in results:
        preview = text[:50] + ('...' if len(text) > 50 else '')
        print(f"{line_num:<8} {preview:<55} {context}")

    print(f"\n📝 Всего: {len(results)} строк")


if __name__ == "__main__":
    import sys
    main()
