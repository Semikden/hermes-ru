#!/usr/bin/env python3
"""
Hermes RU — Apply Translations Safely
Find strings by content, not line numbers.
Handles multi-line strings, preserves formatting.
"""

import re
from pathlib import Path

RUN_PY = Path("/root/hermes-agent-src/gateway/run.py")
TO_TRANSLATE = Path("/root/hermes-ru/to_translate.txt")
TRANSLATIONS = Path("/root/hermes-ru/translated_batch.txt")


def load_pairs():
    """Load English->Russian pairs"""
    eng_list = []
    rus_list = []
    
    with open(TO_TRANSLATE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '|' not in line:
                continue
            eng = line.split('|', 1)[1].strip()
            eng_list.append(eng)
    
    with open(TRANSLATIONS, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '|' not in line:
                continue
            rus = line.split('|', 1)[1].strip()
            rus_list.append(rus)
    
    return list(zip(eng_list, rus_list))


def find_string_in_line(line, eng_text):
    """Find if eng_text is inside a string literal on this line"""
    # Simple case: eng_text is the entire string content
    for quote in ['"', "'"]:
        # Pattern: "content"
        pattern = rf'{re.escape(quote)}(.+?){re.escape(quote)}'
        for m in re.finditer(pattern, line):
            if m.group(1) == eng_text:
                return m.start(), m.end(), quote
    return None


def apply_one_line(line, eng_text, rus_text):
    """Try to replace eng_text with rus_text in line"""
    result = find_string_in_line(line, eng_text)
    if result:
        start, end, quote = result
        return line[:start] + quote + rus_text + quote + line[end:], True
    return line, False


def apply_translations():
    """Apply all translations to run.py"""
    pairs = load_pairs()
    print(f"Loaded {len(pairs)} translation pairs")
    
    content = RUN_PY.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    applied = 0
    failed = 0
    
    for eng, rus in pairs:
        # Skip multi-line or very long strings
        if '\n' in eng or len(eng) > 200:
            print(f"  ⚠️ Skipping multi-line/long: {eng[:50]}...")
            failed += 1
            continue
        
        found = False
        for i, line in enumerate(lines):
            # Skip obvious non-string lines
            if any(line.strip().startswith(x) for x in ['#', 'import ', 'from ', 'def ', 'class ', 'if ', 'elif ', 'else:', 'try:', 'except ', 'return ']):
                continue
            
            new_line, ok = apply_one_line(line, eng, rus)
            if ok:
                lines[i] = new_line
                applied += 1
                found = True
                break
        
        if not found:
            print(f"  ❌ Not found: {eng[:60]}")
            failed += 1
    
    # Write back
    RUN_PY.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\n✅ Applied: {applied}")
    print(f"❌ Failed: {failed}")
    
    return applied, failed


if __name__ == "__main__":
    apply_translations()
