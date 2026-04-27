#!/usr/bin/env python3
"""
Hermes Telegram RU — Audit Script
Находит все English строки в gateway/run.py которые отправляются в чат (Telegram и др. платформы).
НЕ затрагивает CLI-строки.

Использование:
    python3 audit_ru.py

Вывод: список непереведённых строк с номерами строк.
"""

import re
import sys
from pathlib import Path

# Путь к run.py
RUN_PY = Path.home() / ".hermes" / "hermes-agent" / "gateway" / "run.py"

# Альтернативный путь (если hermes-agent установлен через pip)
ALT_PATHS = [
    Path("/root/hermes-agent-src/gateway/run.py"),
    Path.home() / "hermes-agent-src" / "gateway" / "run.py",
]

def find_run_py():
    if RUN_PY.exists():
        return RUN_PY
    for p in ALT_PATHS:
        if p.exists():
            return p
    return None

def audit_telegram_strings(filepath: Path) -> list:
    """Находит English строки отправляемые в адаптеры (chat-платформы)."""
    
    content = filepath.read_text()
    lines = content.split('\n')
    
    results = []
    
    # Паттерны для поиска:
    # 1. adapter.send(chat_id, "English string")
    # 2. f"English string" с emoji prefix (⏳, ⚡, 📬, ♻ и т.д.)
    # 3. return "English string" если это response для чата
    
    # Игнорируемые паттерны (CLI):
    # - logger.info/warning/error (это логи)
    # - skin_emojis, skin_engine
    # - CLI help text
    
    # Паттерны для поиска English строк в adapter.send и return
    patterns = [
        # adapter.send(..., "English", ...)
        (r'await adapter\.send\([^)]*"([A-Z][^"]+)"', 'adapter.send'),
        # return "English"  (но не logger. и не CLI)
        (r'return ("[◐⏳⚡📬♻][^"]*")', 'return'),
        # progress_queue.put("English")
        (r'progress_queue\.put\("([^"]+)"\)', 'progress_queue'),
        # f"English" после emoji prefix в Telegram context
        (r'(["\'])([A-Z][a-z].*?)\1(?=\s*[,\)])', 'inline'),
    ]
    
    # Более точный подход: ищем все строки с английскими словами в конце
    # которые отправляются в чат
    
    chat_strings = []
    
    for i, line in enumerate(lines, 1):
        # Пропускаем комментарии
        if re.match(r'^\s*#', line):
            continue
        
        # Пропускаем logger.* — это CLI/логи
        if re.search(r'logger\.(info|warning|error|debug)', line):
            continue
        
        # Пропускаем CLI help
        if 'slash command' in line.lower() or 'usage:' in line.lower():
            continue
        
        # Ищем adapter.send и progress_queue.put
        if 'adapter.send' in line or 'progress_queue.put' in line:
            # Извлекаем строки в кавычках
            strings = re.findall(r'"([^"]+)"', line)
            for s in strings:
                # Фильтруем: пропускаем переменные, пути, технический текст
                s_stripped = s.strip()
                if not s_stripped:
                    continue
                # Пропускаем если уже есть русские буквы
                if any('\u0400' <= c <= '\u04FF' for c in s_stripped):
                    continue
                # Пропускаем технические строки (содержат переменные, пути и т.д.)
                if re.search(r'[{}%$]', s_stripped):
                    continue
                # Пропускаем очень короткие строки
                if len(s_stripped) < 5:
                    continue
                # Пропускаем строки с file path
                if '/' in s_stripped and ('.' in s_stripped):
                    continue
                chat_strings.append((i, s_stripped))
    
    # Также ищем return с русскими emoji но English текстом
    for i, line in enumerate(lines, 1):
        if 'return' not in line:
            continue
        if re.search(r'logger', line):
            continue
        
        # Ищем return f"..." или return "..."
        matches = re.findall(r'return [f]?"([^"]+)"', line)
        for m in matches:
            m_stripped = m.strip()
            if not m_stripped:
                continue
            # Если есть русские буквы — ок
            if any('\u0400' <= c <= '\u04FF' for c in m_stripped):
                continue
            # Содержит переменные
            if '{' in m_stripped and '}' in m_stripped:
                continue
            if len(m_stripped) < 5:
                continue
            # English строка в return
            chat_strings.append((i, m_stripped))
    
    # Уникальные результаты
    seen = set()
    unique = []
    for line_num, text in chat_strings:
        key = (line_num, text)
        if key not in seen:
            seen.add(key)
            unique.append((line_num, text))
    
    return sorted(unique, key=lambda x: x[0])


def main():
    filepath = find_run_py()
    
    if not filepath:
        print("❌ run.py не найден!")
        print("   Ожидаемые пути:")
        print(f"   - {RUN_PY}")
        for p in ALT_PATHS:
            print(f"   - {p}")
        sys.exit(1)
    
    print(f"🔍 Аудит: {filepath}")
    print("=" * 60)
    
    results = audit_telegram_strings(filepath)
    
    if not results:
        print("✅ Все строки переведены!")
        return
    
    print(f"❌ Найдено {len(results)} непереведённых строк:\n")
    
    for line_num, text in results:
        print(f"  Строка {line_num}: {text[:80]}{'...' if len(text) > 80 else ''}")
    
    print("\n" + "=" * 60)
    print("Для перевода — добавь в словарь _RU в progress_callback")
    print("или патчи соответствующие строки в run.py")


if __name__ == "__main__":
    main()
