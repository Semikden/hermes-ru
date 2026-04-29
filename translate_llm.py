#!/usr/bin/env python3
"""
Hermes RU — LLM Batch Translator
Переводит English строки в Russian через MiniMax API.
Сохраняет результат в translated.txt
"""

import json
import os
import urllib.request
from pathlib import Path
from typing import List, Tuple, Optional

INPUT_FILE = Path("/root/hermes-ru/found_strings.txt")
OUTPUT_FILE = Path("/root/hermes-ru/translated.txt")


def load_strings() -> List[Tuple[str, int, str]]:
    """Load strings from found_strings.txt"""
    if not INPUT_FILE.exists():
        print(f"❌ Файл не найден: {INPUT_FILE}")
        return []
    
    strings = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|', 2)
            if len(parts) == 3:
                filepath, line_num, text = parts
                strings.append((filepath, int(line_num), text))
    
    return strings


def call_llm(prompt: str, api_key: str) -> Optional[str]:
    """Call MiniMax API"""
    url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    
    payload = {
        "model": "MiniMax-Text-01",
        "messages": [
            {"role": "system", "content": "You are a professional translator. Translate English strings to Russian for a chat application. Keep emoji, markdown formatting (*bold*, _italic_), {variables}, [placeholders] intact. Reply ONLY with valid JSON: {\"filepath|line\": \"translation\"}"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"   ❌ API error: {e}")
        return None


def translate_batch(strings: List[Tuple[str, int, str]], batch_size: int = 25) -> dict:
    """Translate strings in batches via LLM"""
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key:
        print("❌ MINIMAX_API_KEY не установлен")
        return {}
    
    results = {}
    
    # Process in batches
    for i in range(0, len(strings), batch_size):
        batch = strings[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(strings) + batch_size - 1) // batch_size
        print(f"\n📡 Batch {batch_num}/{total_batches}: перевожу {len(batch)} строк...")
        
        # Build prompt
        prompt_lines = ["Translate to Russian. Keep all formatting: emoji, markdown, {variables}."]
        prompt_lines.append("Reply JSON only: {\"filepath|line\": \"russian_translation\"}")
        prompt_lines.append("")
        
        for filepath, line_num, text in batch:
            key = f"{filepath}|{line_num}"
            # Escape for JSON
            text_escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            prompt_lines.append(f'"{key}": "{text_escaped}"')
        
        prompt = "\n".join(prompt_lines)
        response = call_llm(prompt, api_key)
        
        if not response:
            print(f"   ⚠️ Batch {batch_num} пропущен")
            continue
        
        # Parse JSON response
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                translations = json.loads(response[start:end])
                results.update(translations)
                print(f"   ✅ {len(translations)} переводов")
        except json.JSONDecodeError as e:
            print(f"   ❌ Parse error: {e}")
            # Save raw response for debugging
            debug_file = Path(f"/root/hermes-ru/debug_batch_{batch_num}.txt")
            debug_file.write_text(response)
            print(f"   📝 Сохранено в {debug_file}")
            continue
    
    return results


def main():
    print("🔄 Hermes RU — LLM Batch Translator")
    print("=" * 50)
    
    strings = load_strings()
    if not strings:
        print("❌ Нет строк для перевода. Сначала запусти find_en_strings.py")
        return
    
    print(f"📊 Загружено строк: {len(strings)}")
    
    translations = translate_batch(strings)
    
    if not translations:
        print("❌ Перевод не получен")
        return
    
    # Save results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# {len(translations)} translations\n\n")
        for key, translation in sorted(translations.items()):
            f.write(f"{key}|{translation}\n")
    
    print(f"\n✅ Сохранено {len(translations)} переводов в {OUTPUT_FILE}")
    print("📋 Следующий шаг: apply_safe.py")


if __name__ == "__main__":
    main()
