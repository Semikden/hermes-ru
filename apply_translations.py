#!/usr/bin/env python3
"""
Hermes Telegram RU — Apply Translations v3
Применяет переводы из translations.txt к run.py

Использование:
    python3 apply_translations.py
"""

import re
from pathlib import Path

RUN_PY = Path("/root/hermes-agent-src/gateway/run.py")
TRANS_FILE = Path("/root/hermes-ru/translations.txt")
BACKUP_FILE = Path("/root/hermes-agent-src/gateway/run.py.ru_backup")


def load_translations():
    """Загружает переводы из файла. \\n сохраняется как-is (не как newline)."""
    translations = {}
    if not TRANS_FILE.exists():
        print(f"❌ {TRANS_FILE} не найден!")
        return {}

    content = TRANS_FILE.read_text(encoding='utf-8')
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '|' not in line:
            continue
        parts = line.split('|', 1)
        if len(parts) != 2:
            continue
        line_num = parts[0].strip()
        text = parts[1].strip()
        # \\n остаётся как \\n (backslash+n) — это валидный Python escape
        translations[line_num] = text

    return translations


def apply_translations():
    """Применяет переводы к run.py"""
    translations = load_translations()
    if not translations:
        print("❌ Нет переводов")
        return False

    if not RUN_PY.exists():
        print(f"❌ {RUN_PY} не найден!")
        return False

    # Бекап
    BACKUP_FILE.write_text(RUN_PY.read_text(encoding='utf-8'), encoding='utf-8')
    print(f"✅ Бекап: {BACKUP_FILE}")

    content = RUN_PY.read_text(encoding='utf-8')
    lines = content.split('\n')

    applied = 0
    skipped_vars = []
    skipped_other = []

    for line_num_str, russian_text in translations.items():
        line_idx = int(line_num_str) - 1
        if not (0 <= line_idx < len(lines)):
            skipped_other.append(f"Строка {line_num_str}: вне диапазона")
            continue

        original_line = lines[line_idx]

        # Пропускаем если уже русский
        if any('\u0400' <= c <= '\u04FF' for c in original_line):
            continue

        # Пропускаем если internal
        if 'logger.' in original_line or '__dedup__' in original_line:
            continue

        # Вариант 1: return "text" или return f"text"
        m = re.search(r'(return [f]?")([^"]+)(")', original_line)
        if m:
            original_text = m.group(2)
            if '{' in original_text and '}' in original_text:
                skipped_vars.append(line_num_str)
            else:
                new_line = original_line.replace(original_text, russian_text)
                lines[line_idx] = new_line
                applied += 1
            continue

        # Вариант 2: adapter.send(chat_id, "text")
        m = re.search(r'(adapter\.send\([^)]+?,\s*")([^"]+)("\))', original_line)
        if m:
            original_text = m.group(2)
            if '{' in original_text and '}' in original_text:
                skipped_vars.append(line_num_str)
            else:
                new_line = original_line.replace(original_text, russian_text)
                lines[line_idx] = new_line
                applied += 1
            continue

        skipped_other.append(f"Строка {line_num_str}: паттерн не найден")

    # Записываем
    RUN_PY.write_text('\n'.join(lines), encoding='utf-8')

    print(f"\n✅ Применено: {applied}")
    if skipped_vars:
        print(f"⏭️ С переменными (ручная): {len(skipped_vars)}")
    if skipped_other:
        print(f"⚠️ Другие ({len(skipped_other)}): {', '.join(skipped_other[:5])}")

    return applied > 0


def main():
    print("🚀 Применяю переводы...\n")
    success = apply_translations()
    if success:
        print(f"\n📋 Далее:")
        print("   cd /root/hermes-agent-src && pip install -e .")
        print("   hermes gateway restart")


if __name__ == "__main__":
    main()
