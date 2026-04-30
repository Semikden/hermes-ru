#!/usr/bin/env python3
"""
Batch translate Hermes RU strings via OpenRouter free models.
Keeps {…} f-string placeholders and Telegram markdown intact.
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import List, Tuple

OPENROUTER_API_KEY = "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"
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
- Keep sentence structure natural in Russian
- Keep /command names exactly as-is

Translate ONLY the human-readable text, not placeholders or formatting markers.

Respond with valid JSON: {"translations": [{"en": "...", "ru": "..."}, ...]}

Do not add quotes inside translated strings that would break JSON."""

    user_prompt = json.dumps({"strings": strings}, ensure_ascii=False)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hermes.local",
        "X-Title": "Hermes RU Translator",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
    }

    for attempt in range(MAX_RETRIES):
        try:
            import urllib.request
            req = urllib.request.Request(
                OPENROUTER_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]

                # Try to extract JSON
                # Sometimes model wraps in ```json ... ```
                match = re.search(r"\{[\s\S]*\}", content)
                if match:
                    parsed = json.loads(match.group())
                    return parsed.get("translations", [])
                parsed = json.loads(content)
                return parsed.get("translations", [])

        except Exception as e:
            print(f"  ⚠️  Attempt {attempt+1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return []


def main():
    strings = load_strings()
    if not strings:
        print("No strings to translate. Create unique_strings.txt")
        sys.exit(1)

    translations = load_translations()
    already_done = set(translations.keys())

    # Filter out already translated
    to_translate = [s for s in strings if s not in already_done]
    print(f"Total strings: {len(strings)}")
    print(f"Already done: {len(already_done)}")
    print(f"To translate: {len(to_translate)}")

    if not to_translate:
        print("All done!")
        return

    # Process in batches
    batches = [to_translate[i:i+BATCH_SIZE] for i in range(0, len(to_translate), BATCH_SIZE)]
    print(f"Batches: {len(batches)}")

    for batch_idx, batch in enumerate(batches):
        print(f"\n📦 Batch {batch_idx+1}/{len(batches)} ({len(batch)} strings)")

        result = None
        used_model = None
        for model in FREE_MODELS:
            print(f"  🤖 Trying {model}...")
            result = translate_batch(batch, model)
            if result:
                used_model = model
                break
            print(f"  ⚠️  {model} failed, trying next...")
            time.sleep(5)

        if not result:
            print(f"  ❌ All models failed for this batch!")
            continue

        print(f"  ✅ Got {len(result)} translations via {used_model}")

        for item in result:
            en = item.get("en", "")
            ru = item.get("ru", "")
            if en and ru:
                translations[en] = ru

        save_translations(translations)
        print(f"  💾 Saved {len(translations)} total translations")

        # Rate limit between batches
        if batch_idx < len(batches) - 1:
            time.sleep(3)

    print(f"\n✅ Done! {len(translations)} strings translated")
    print(f"📁 Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
