#!/usr/bin/env python3
"""
Hermes RU — Safe Apply with Backup
Применяет переводы с валидацией и бэкапом.
Бэкапит оригинальные файлы перед изменениями.
"""

import ast
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

INPUT_FILE = Path("/root/hermes-ru/translated.txt")
BACKUP_DIR = Path("/root/hermes-ru/backups")


def load_translations() -> Dict[Tuple[str, int], str]:
    """Load translations from translated.txt"""
    if not INPUT_FILE.exists():
        print(f"❌ Файл не найден: {INPUT_FILE}")
        return {}
    
    translations = {}
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.rsplit('|', 1)
            if len(parts) == 2:
                key, translation = parts
                key_parts = key.rsplit('|', 1)
                if len(key_parts) == 2:
                    filepath, line_num = key_parts
                    try:
                        translations[(filepath, int(line_num))] = translation
                    except ValueError:
                        continue
    
    return translations


def create_backup(filepath: Path) -> Path:
    """Create timestamped backup"""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{filepath.name}.{timestamp}.bak"
    backup_path.write_bytes(filepath.read_bytes())
    print(f"   💾 Бэкап: {backup_path.name}")
    return backup_path


def validate_python_syntax(filepath: Path) -> bool:
    """Check Python syntax before applying"""
    try:
        ast.parse(filepath.read_text(encoding='utf-8'))
        return True
    except SyntaxError as e:
        print(f"   ❌ Синтаксическая ошибка: {e}")
        return False


def apply_translations(translations: Dict[Tuple[str, int], str]) -> Tuple[int, int]:
    """Apply translations to source files"""
    applied = 0
    failed = 0
    
    # Group by file
    by_file: Dict[str, List[Tuple[int, str]]] = {}
    for (filepath, line_num), translation in translations.items():
        if filepath not in by_file:
            by_file[filepath] = []
        by_file[filepath].append((line_num, translation))
    
    for filepath_str, edits in by_file.items():
        filepath = Path(filepath_str)
        if not filepath.exists():
            print(f"\n⚠️ Файл не найден: {filepath}")
            failed += len(edits)
            continue
        
        print(f"\n📄 {filepath.name}...")
        
        # Backup
        backup_path = create_backup(filepath)
        
        # Load content
        lines = filepath.read_text(encoding='utf-8').split('\n')
        
        # Apply edits (sort descending to not shift line numbers)
        edits_sorted = sorted(edits, key=lambda x: x[0], reverse=True)
        
        for line_num, translation in edits_sorted:
            idx = line_num - 1  # 0-indexed
            if 0 <= idx < len(lines):
                old_line = lines[idx]
                # Simple approach: replace the line content while keeping indentation
                indent = len(old_line) - len(old_line.lstrip())
                indent_str = old_line[:indent]
                lines[idx] = f'{indent_str}"{translation}"'
                applied += 1
                print(f"   ✅ {line_num}: {translation[:50]}{'...' if len(translation) > 50 else ''}")
            else:
                print(f"   ❌ Строка {line_num} вне диапазона")
                failed += 1
        
        # Write back
        filepath.write_text('\n'.join(lines), encoding='utf-8')
        
        # Validate
        if validate_python_syntax(filepath):
            print(f"   ✅ Синтаксис OK")
        else:
            print(f"   ❌ Синтаксис сломан — откат...")
            # Restore from backup
            filepath.write_bytes(backup_path.read_bytes())
            failed += 1
            applied -= 1
    
    return applied, failed


def main():
    print("🔄 Hermes RU — Safe Apply")
    print("=" * 50)
    
    translations = load_translations()
    if not translations:
        print("❌ Нет переводов. Сначала запусти find_en_strings.py → translate_llm.py")
        return
    
    print(f"📊 Загружено переводов: {len(translations)}")
    
    # Create main backup
    print("\n💾 Создаю бэкап...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_backup = BACKUP_DIR / f"pre_translate_{timestamp}"
    main_backup.mkdir(exist_ok=True)
    
    for src in Path("/root/hermes-agent-src").rglob("*.py"):
        if 'venv' not in str(src) and '__pycache__' not in str(src):
            backup_file = main_backup / src.name
            backup_file.write_bytes(src.read_bytes())
    
    print(f"   ✅ Бэкап: {main_backup}/")
    
    # Apply
    print("\n✏️ Применяю переводы...")
    applied, failed = apply_translations(translations)
    
    print("\n" + "=" * 50)
    print(f"✅ Применено: {applied}")
    print(f"❌ Ошибок: {failed}")
    
    if failed == 0:
        print("\n🎉 Все переводы применены успешно!")
        print("📋 Для активации: hermes gateway restart")


if __name__ == "__main__":
    main()
