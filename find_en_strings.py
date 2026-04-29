#!/usr/bin/env python3
"""
Hermes RU — Find User-Facing English Strings
Находит ТОЛЬКО English строки которые показываются пользователю в чате/Telegram/Discord.
НЕ переводит: ENV vars, config keys, code, terminal commands.
"""

import re
from pathlib import Path
from typing import List, Tuple

SOURCE_FILES = [
    Path("/root/hermes-agent-src/gateway/run.py"),
]

# Absolutely SKIP these patterns (technical, not user-facing)
SKIP_PATTERNS = [
    r'^import ',
    r'^from ',
    r'^\s*#',
    r'except\s+\w+',
    r'raise\s+\w+',
    r'if\s+__name__',
    r'def\s+\w+',
    r'class\s+\w+',
    r'self\.',
    r'\.send\(',
    r'return\s+{',
    r'template=',
    r'prompt=',
    r'messages=',
    r'--help',
    r'--version',
    r'^Usage:',
    r'\[.*?\]\s*=',
    r'(?:TERMINAL|AUXILIARY|GATEWAY|HERMES|OPENAI|ANTHROPIC|AZURE)_[A-Z]',
    r'SSL_CERT',
    r'HTTP_PROXY',
    r'https?://',
    r'^\s{0,4}"[\$\{]',
    r'^"[\$\{]',
    r'^\s*/',
    r'^\s+\.',
    r'^\s*#',
    r'^\s*$',
    r'^\s*""".*"""',  # Docstrings
    r'^[A-Z_]{5,}$',  # CONSTANTS like TERMINAL_TIMEOUT
    r'^[a-z_]+\.[a-z_]+',  # snake_case identifiers
    r'\bdef\s+\w+\(',
    r'\bif\s+\w+\s*[!=]=',
    r'\bfor\s+\w+\s+in\s+',
    r'\bwhile\s+\w+',
    r'try:\s*$',
    r'except\s+\w+:',
    r'match\s+\w+:',
    r'case\s+\w+:',
    r'yield\s+',
    r'return\s+None',
    r'return\s+\w+',
    r'assert\s+',
    r'\w+\s*=\s*\[',  # list assignments
    r'\w+\s*=\s*\{',  # dict assignments
    r'\w+\s*=\s*"',  # string assignments
    r'\w+\s*=\s*\'',  # string assignments
]

# MUST have these to be considered user-facing (chat message indicators)
USER_FACING_INDICATORS = [
    r'[А-Яа-яЁё]',  # Has Russian (already translated?)
    r'⚡|✅|❌|⚠️|🧠|📌|🔄|✏️|↩️|↻|✗|🎭|💾|📡|📝|🔍',  # Emoji at start (chat messages)
    r'^\s*[?!.]{1,2}\s',  # Starts with punctuation
    r'^/[^ ]',  # Command help like "/help"
    r'^\*\*',  # Markdown bold
    r'^_',  # Markdown italic
    r'\[[0-9]+\]:',  # Link-style [1]: format
]

# Must NOT be too code-like
def is_code_heavy(text: str) -> bool:
    """Check if text looks more like code than a message"""
    # Has many underscores in a row
    if '__' in text:
        return True
    # Has = without spaces around (assignment)
    if re.search(r'\w=\w', text) and not re.search(r'[?!.]$', text):
        return True
    # All caps with underscores (CONSTANTS)
    if re.match(r'^[A-Z][A-Z0-9_]+$', text):
        return True
    # Very short (1-2 chars)
    if len(text.strip()) <= 2:
        return True
    # Path-like
    if '/' in text and ('.' in text or 'etc' in text or 'var' in text):
        return True
    # URL-like
    if '://' in text or re.match(r'^https?://', text):
        return True
    # env var pattern
    if re.match(r'^[A-Z][A-Z0-9_]*=', text):
        return True
    return False


def is_user_facing(text: str) -> bool:
    """Check if string is a user-facing message"""
    text = text.strip()
    
    # Skip empty
    if len(text) < 2:
        return False
    
    # Skip if too code-like
    if is_code_heavy(text):
        return False
    
    # Skip if matches skip patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text):
            return False
    
    # Must have at least one user-facing indicator
    has_indicator = False
    for pattern in USER_FACING_INDICATORS:
        if re.search(pattern, text):
            has_indicator = True
            break
    
    # OR has substantial English text with sentence structure
    if not has_indicator:
        # Check for natural language indicators
        english_words = len(re.findall(r'[a-zA-Z]{3,}', text))
        sentence_chars = len(re.findall(r'[.!?]', text))
        
        # Has periods, question marks, exclamation marks (sentence)
        has_sentence_structure = sentence_chars >= 1
        
        # Has multiple words
        has_multiple_words = len(text.split()) >= 2
        
        # Looks like a message (not a keyword)
        looks_like_message = (
            re.search(r'\s', text) and  # has spaces
            (re.search(r'[.!?]$', text) or re.search(r'^[A-Z][a-z]', text))  # ends with punct or starts with capital
        )
        
        if not (has_sentence_structure or looks_like_message):
            return False
    
    return True


def extract_strings_from_line(line: str) -> List[str]:
    """Extract string literals from a line that look user-facing"""
    results = []
    
    # Match both single and double quotes
    for match in re.finditer(r'''(['"])([^'"]+)\1''', line):
        text = match.group(2)
        if text and is_user_facing(text):
            results.append(text)
    
    return results


def find_strings_in_file(filepath: Path) -> List[Tuple[int, str]]:
    """Find all user-facing English strings in a file"""
    if not filepath.exists():
        print(f"⚠️ Файл не найден: {filepath}")
        return []
    
    results = []
    lines = filepath.read_text(encoding='utf-8').split('\n')
    
    for i, line in enumerate(lines, 1):
        strings = extract_strings_from_line(line)
        for text in strings:
            results.append((i, text))
    
    return results


def main():
    print("🔍 Hermes RU — Find User-Facing Strings")
    print("=" * 50)
    
    all_strings = []
    
    for filepath in SOURCE_FILES:
        print(f"\n📄 {filepath.name}...")
        strings = find_strings_in_file(filepath)
        print(f"   Найдено: {len(strings)}")
        
        for line_num, text in strings:
            all_strings.append((str(filepath), line_num, text))
            # Show first 70 chars
            display = text[:70] + '...' if len(text) > 70 else text
            print(f"   {line_num}: {display}")
    
    # Save to file
    output = Path("/root/hermes-ru/found_strings.txt")
    with open(output, 'w', encoding='utf-8') as f:
        f.write(f"# Found {len(all_strings)} user-facing strings\n\n")
        for filepath, line_num, text in all_strings:
            f.write(f"{filepath}|{line_num}|{text}\n")
    
    print(f"\n✅ Сохранено в {output}")
    print(f"📊 Всего: {len(all_strings)}")
    
    return all_strings


if __name__ == "__main__":
    main()
