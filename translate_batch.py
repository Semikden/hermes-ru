#!/usr/bin/env python3
"""
Batch translate Hermes RU strings via OpenRouter free models.
Keeps {…} f-string placeholders and Telegram markdown intact.
"""

import json
import re
import sys
import time
import os
from pathlib import Path
from typing import List, Tuple

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free models in preferred order
FREE_MODELS = [
    "gpt-oss-120b:free",
    "mimo-v2-flash",
    "nemotron-3-super-120b:free",
]

INPUT_FILE = Path("/root/hermes-ru/unique_strings.txt")
OUTPUT_FILE = Path("/root/hermes-ru/translated_strings.json")
BATCH_SIZE = 25  # strings per request
MAX_RETRIES = 3
RETRY_DELAY = 10


def save_strings(strings: List[str]):
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        for s in strings:
            f.write(s + "\n")


def load_strings() -> List[str]:
    if not INPUT_FILE.exists():
        return []
    return [l.strip() for l in INPUT_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_translations() -> dict:
    if not OUTPUT_FILE.exists():
        return {}
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_translations(translations: dict):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(translations, f, ensure_ascii=False, indent=2)


def translate_batch(strings: List[str], model: str) -> dict:
    """Translate a batch of strings via OpenRouter."""
    system_prompt = """You are a translator. Translate Telegram/chat user-facing messages from English to Russian.

RULES:
- Keep ALL {…} f-string placeholders EXACTLY as-is (e.g. {skill_name}, {…}, {X})
- Keep Telegram markdown: **bold**, `code`, *italic*, **bold**, {…} placeholders
- Keep emoji at the start of messages EXACTLY as-is
- Keep {skill_name} style placeholders, only translate surrounding text
- Keep `backtick` formatting for commands, code, variables
- Keep [link](url) markdown intact
- Output valid JSON only: {"string": "translation"}
"""

    user_prompt = "\n".join(f'"{s}": ""' for s in strings)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Translate to Russian:\n{user_prompt}"},
        ],
        "temperature": 0.3,
    }

    for attempt in range(MAX_RETRIES):
        try:
            import urllib.request
            req = urllib.request.Request(
                OPENROUTER_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://hermes-ru",
                    "X-Title": "Hermes RU Translator",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                content = result["choices"][0]["message"]["content"]

                # Parse JSON
                start = content.find("{")
                end = content.rfind("}") + 1
                if start != -1 and end != 0:
                    return json.loads(content[start:end])
                print(f"   ⚠️ No JSON in response, got: {content[:200]}")
                return {}
        except Exception as e:
            print(f"   ⚠️ Attempt {attempt+1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    return {}


def main():
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not set")
        sys.exit(1)

    strings = load_strings()
    if not strings:
        print("❌ No strings to translate")
        sys.exit(1)

    print(f"📊 Loaded {len(strings)} strings")

    existing = load_translations()
    done = set(existing.keys())
    remaining = [s for s in strings if s not in done]
    print(f"📊 {len(done)} already translated, {len(remaining)} to go")

    results = dict(existing)
    current_model = 0

    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE

        # Try current model, fallback to next
        for offset in range(len(FREE_MODELS)):
            model = FREE_MODELS[(current_model + offset) % len(FREE_MODELS)]
            print(f"\n📡 Batch {batch_num}/{total_batches} via {model}...")
            batch_results = translate_batch(batch, model)
            if batch_results:
                results.update(batch_results)
                save_translations(results)
                print(f"   ✅ {len(batch_results)} translated ({len(results)} total)")
                current_model = (current_model + offset) % len(FREE_MODELS)
                break
            print(f"   ⚠️ {model} failed, trying next...")
            time.sleep(RETRY_DELAY)
        else:
            print(f"   ❌ All models failed for batch {batch_num}")

    print(f"\n✅ Done: {len(results)}/{len(strings)} strings translated")
    save_translations(results)


if __name__ == "__main__":
    main()