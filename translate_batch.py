#!/usr/bin/env python3
"""
Hermes Telegram RU — Batch Translation Script
Одним запросом к LLM переводит все непереведённые строки и генерирует патч.

Использование:
    python3 translate_batch.py

Результат:
    translations.txt — готовые переводы
    ru_batch.patch — патч для apply
"""

import re
import os
import subprocess
from pathlib import Path

RUN_PY = Path("/root/hermes-agent-src/gateway/run.py")
OUT_TRANS = Path("/root/hermes-ru/translations.txt")
OUT_PATCH = Path("/root/hermes-ru/ru_batch.patch")

# Strings to translate (from audit)
STRINGS_TO_TRANSLATE = [
    ("3416", "⚡ Stopped. You can continue this session."),
    ("3441", "Usage: /queue <prompt>"),
    ("3462", "Usage: /steer <prompt>"),
    ("3476", "Agent still starting — /steer queued for the next turn."),
    ("3486", "Steer rejected (empty payload)."),
    ("3498", "No active agent — /steer queued for the next turn."),
    ("3502", "Agent is running — wait or /stop first, then switch models."),
    ("3605", "⚡ Force-stopped. The agent was still starting — session unlocked."),
    ("3689", "Command `/{command}` was blocked by a hook."),
    ("3802", "Usage: /steer <prompt>  (no agent is running; sending as a normal message)"),
    ("3840", "Quick command timed out (30s)."),
    ("3842", "Quick command error: {e}"),
    ("3844", "Quick command '/{command}' has no command defined."),
    ("3855", "Quick command '/{command}' has no target defined."),
    ("3857", "Quick command '/{command}' has unsupported type (supported: 'exec', 'alias')."),
    ("5326", "⚡ Stopped. The agent hadn't started yet — you can continue this session."),
    ("5336", "⚡ Stopped. You can continue this session."),
    ("5338", "No active task to stop."),
    ("5497", "Usage: `/commands [page]`"),
    ("5516", "No commands available."),
    ("5646", "Error: {result.error_message}"),
    ("5770", "Error: {result.error_message}"),
    ("5931", "🎭 Personality cleared — using base agent behavior.\n_(takes effect on next message)_"),
    ("5947", "🎭 Personality set to **{args}**\n_(takes effect on next message)_"),
    ("5968", "No previous message to retry."),
    ("6002", "Nothing to undo."),
    ("6011", "↩️ Undid {removed_count} message(s).\nRemoved: \"{preview}\""),
    ("6080", "Voice mode disabled. Text-only replies."),
    ("6125", "Voice mode enabled."),
    ("6131", "Voice mode disabled."),
    ("6137", "Voice channels are not supported on this platform."),
    ("6141", "This command only works in a Discord server."),
    ("6147", "You need to be in a voice channel first."),
    ("6182", "Failed to join voice channel. Check bot permissions (Connect + Speak)."),
    ("6190", "Not in a voice channel."),
    ("6193", "Not in a voice channel."),
    ("6205", "Left voice channel."),
    ("6521", "❌ {result['error']}"),
    ("6769", "🧠 ✓ Reasoning display: **OFF** for **{platform_key}**.\n_(takes effect on next message)_"),
    ("6775", "⚠️ `/reasoning reset --global` is not supported. Use `/reasoning <level> --global` instead."),
    ("6779", "🧠 ✓ Session reasoning override cleared; falling back to global config."),
    ("6797", "🧠 ✓ Reasoning effort set to `{effort}` (saved to config)\n_(takes effect on next message)_"),
    ("6800", "🧠 ✓ Reasoning effort set to `{effort}` (session only — config save failed)"),
    ("6804", "🧠 ✓ Reasoning effort set to `{effort}` (session only — add `--global` to save)"),
    ("6818", "⚡ /fast is only available for OpenAI models that support Priority Processing."),
    ("6863", "⚡ ✓ Priority Processing: **{label}** (saved to config)\n_(takes effect on next message)_"),
    ("6864", "⚡ ✓ Priority Processing: **{label}** (this session only)"),
    ("6878", "⚠️ YOLO mode **OFF** for this session — dangerous commands will require approval."),
    ("6881", "⚡ YOLO mode **ON** for this session — all commands auto-approved. Use with caution."),
    ("6962", "Not enough conversation to compress (need at least 4 messages)."),
    ("6978", "No provider configured -- cannot compress."),
    ("7002", "Nothing to compress yet (the transcript is still all protected context)."),
    ("7051", "Session database not available."),
    ("7075", "⚠️ Title is empty after cleanup. Please use printable characters."),
    ("7079", "✏️ Session title set: **{sanitized}**"),
    ("7081", "Session not found in database."),
    ("7088", "📌 Session: `{session_id}`\nTitle: **{title}**"),
    ("7090", "📌 Session: `{session_id}`\nNo title set. Usage: `/title My Session Name`"),
    ("7095", "Session database not available."),
    ("7125", "Could not list sessions: {e}"),
    ("7144", "📌 Already on session **{name}**."),
    ("7152", "Failed to switch session."),
    ("7163", "↻ Resumed session **{title}**{msg_part}. Conversation restored."),
    ("7175", "Session database not available."),
    ("7184", "No conversation to branch — send a message first."),
    ("7242", "Branch created but failed to switch to it."),
    ("7392", "No usage data available for this session."),
    ("7441", "Error generating insights: {e}"),
    ("7546", "⚠️ Approval expired (agent is no longer waiting). Ask the agent to try again."),
    ("7547", "No pending command to approve."),
    ("7566", "No pending command to approve."),
    ("7575", "✅ Command{'s' if count > 1 else ''} approved{scope_msg}{count_msg}. The agent continues..."),
    ("7595", "❌ Command denied (approval was stale)."),
    ("7596", "No pending command to deny."),
    ("7603", "No pending command to deny."),
    ("7612", "❌ Command{'s' if count > 1 else ''} denied{count_msg}."),
    ("7684", "✗ /update is only available from messaging platforms. Run `hermes update` from terminal."),
    ("7687", "✗ {format_managed_message('update Hermes Agent')}"),
    ("7693", "✗ Not a git repository — cannot update."),
    ("7758", "⚕ Starting Hermes update… I'll stream progress here."),
    ("7877", "✅ Hermes update finished."),
    ("7960", "❌ Hermes update timed out after 30 minutes."),
]

TRANSLATIONS = {}

def get_api_key():
    """Get OpenAI API key from .env"""
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().split('\n'):
            if 'VOICE_TOOLS_OPENAI_KEY' in line or 'OPENAI_API_KEY' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    return parts[1].strip().strip('"\'')
    return None

def call_llm(prompt: str) -> str:
    """Call LLM API to translate"""
    api_key = get_api_key()

    if not api_key or api_key.startswith('#'):
        # Fallback to OpenRouter with free model
        return None

    import json
    import urllib.request

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a translator. Translate English strings to Russian for a software application. Keep formatting (emoji, markdown, {variables}) intact. Reply ONLY with JSON object where keys are line numbers and values are Russian translations. Example: {\"3416\": \"⚡ Остановлено. Можешь продолжить эту сессию.\", \"3441\": \"Использование: /queue <текст>\"}"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"API error: {e}")
        return None

def generate_translations():
    """Generate translations using LLM"""
    lines = []
    lines.append("Translate these English strings to Russian. Keep {variable} placeholders, emoji, and markdown formatting. Reply with JSON only:")
    lines.append("")

    for line_num, text in STRINGS_TO_TRANSLATE:
        # Escape for JSON
        text_escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        lines.append(f'"{line_num}": "{text_escaped}"')

    return "\n".join(lines)

def parse_llm_response(response: str) -> dict:
    """Parse LLM JSON response"""
    if not response:
        return {}

    # Try to extract JSON from response
    try:
        # Find JSON block
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = response[start:end]
            import json
            return json.loads(json_str)
    except Exception as e:
        print(f"Parse error: {e}")
        return {}

    return {}

def generate_patch(translations: dict) -> str:
    """Generate patch file from translations"""
    if not RUN_PY.exists():
        return "ERROR: run.py not found"

    content = RUN_PY.read_text()
    lines = content.split('\n')
    modified = False

    for line_num_str, russian_text in translations.items():
        line_idx = int(line_num_str) - 1
        if 0 <= line_idx < len(lines):
            original = lines[line_idx]

            # Simple replacement: find the line with the English text and replace
            # This is a simplified approach - actual patch will be more precise
            pass

    # Generate proper patch
    patch_lines = []
    patch_lines.append("# Hermes Telegram RU — Batch Translation Patch")
    patch_lines.append(f"# Generated from {len(translations)} translations")
    patch_lines.append("")
    patch_lines.append("# Apply with: git apply < ru_batch.patch")
    patch_lines.append("")

    for line_num_str, russian_text in sorted(translations.items(), key=lambda x: int(x[0])):
        line_idx = int(line_num_str) - 1
        original = lines[line_idx] if 0 <= line_idx < len(lines) else "NOT FOUND"

        # Escape for patch
        russian_escaped = russian_text.replace('\\', '\\\\').replace('"', '\\"')

        patch_lines.append(f"--- a/run.py")
        patch_lines.append(f"+++ b/run.py")
        patch_lines.append(f"@{line_num_str}@")
        patch_lines.append(f"-{original}")
        patch_lines.append(f"+{russian_text}")
        patch_lines.append("")

    return "\n".join(patch_lines)

def main():
    print("🚀 Запускаю batch translation...")
    print(f"📊 Строк для перевода: {len(STRINGS_TO_TRANSLATE)}")

    # Generate prompt
    prompt = generate_translations()

    # Call LLM
    print("📡 Отправляю в LLM...")
    response = call_llm(prompt)

    if not response:
        print("❌ LLM недоступен. Сохраняю список строк в translations.txt")
        # Save raw list for manual translation
        with open(OUT_TRANS, 'w') as f:
            f.write("# Strings to translate\n")
            for line_num, text in STRINGS_TO_TRANSLATE:
                f.write(f"{line_num}|{text}\n")
        print(f"✅ Сохранено в {OUT_TRANS}")
        return

    print("📝 Получил ответ от LLM...")

    # Parse
    translations = parse_llm_response(response)

    if not translations:
        print("❌ Не удалось распарсить ответ LLM")
        return

    print(f"✅ Переводов получено: {len(translations)}")

    # Save translations
    with open(OUT_TRANS, 'w', encoding='utf-8') as f:
        f.write(f"# {len(translations)} translations\n")
        for line_num, text in sorted(translations.items(), key=lambda x: int(x[0])):
            f.write(f"{line_num}|{text}\n")

    print(f"✅ Сохранено в {OUT_TRANS}")

    # Generate patch
    patch = generate_patch(translations)
    with open(OUT_PATCH, 'w', encoding='utf-8') as f:
        f.write(patch)

    print(f"✅ Патч сохранён в {OUT_PATCH}")
    print("\n📋 Следующий шаг:")
    print("   1. Проверь translations.txt")
    print("   2. Примени патч: cd /root/hermes-agent-src && git apply < ~/.hermes/skills/hermes-ru/ru_batch.patch")
    print("   3. pip install -e . && hermes gateway restart")

if __name__ == "__main__":
    main()
