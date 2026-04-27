#!/root/hermes-agent/venv/bin/python3
"""
Semantic memory ingest — Python version (uses hermes-agent venv).

Использует hermes-agent credential system для реальных MiniMax API вызовов.
"""
import sys
import json
import re
import time
from pathlib import Path

# Add hermes-agent src to path
sys.path.insert(0, '/root/hermes-agent-src')

from hermes_cli.config import get_env_value
from agent.credential_pool import load_pool, PooledCredential

# ── Constants ────────────────────────────────────────────────────────────────
MINIMAX_BASE_URL = "https://api.minimax.io/v1"
MODEL = "MiniMax-M2.7"
SESSIONS_DIR = Path.home() / ".hermes" / "sessions"
WIKI_DIR = Path("/root/Obsidian/_gera-wiki")
MANIFEST_PATH = WIKI_DIR / ".manifest.json"

SYS_PROMPT = """Ты — система извлечения фактов для долгосрочной памяти AI-агента.

Тебе дана сводка переписки между пользователем (Денис) и AI-агентом (Гера).
Извлеки из неё **новые факты**, которых нет в существующей wiki.

Формат ответа — JSON:
{
  "entities": [
    {"name": "Название", "type": "person|project|tool|concept|location|...", "facts": ["факт 1", "факт 2"]}
  ],
  "decisions": [
    {"topic": "тема", "decision": "что решили", "context": "почему"}
  ],
  "agreements": [
    {"what": "договорённость", "who": "кто", "when": "когда"}
  ],
  "preferences": [
    {"person": "чей профиль", "preference": "что предпочитает", "reason": "почему"}
  ],
  "skills_learned": [
    {"entity": "кто/что", "skill": "новый навык/команда/подход"}
  ],
  "events": [
    {"date": "YYYY-MM-DD", "event": "что произошло", "outcome": "результат"}
  ],
  "open_issues": [
    {"issue": "нерешённый вопрос", "who": "кто должен решить", "priority": "high|medium|low"}
  ]
}

Правила:
- Только проверенные факты из переписки
- Никаких выдуманных деталей
- Если переписка не содержит новых фактов — верни {\"skip\": true}
- facts в entities — конкретные вещи (имена, числа, URL, описания), не абстракции
- Все даты в формате YYYY-MM-DD
- preferences — реальные предпочтения Дениса (язык общения, стиль работы, диетические ограничения и т.д.)
"""

# ── API Call ─────────────────────────────────────────────────────────────────
def call_minimax(prompt: str) -> dict:
    """Make a real MiniMax API call using hermes-agent credentials."""
    import urllib.request
    import urllib.error

    api_key = get_env_value("MINIMAX_API_KEY")
    if not api_key:
        # Try via load_pool
        pool = load_pool()
        entries = [e for e in pool.entries if e.provider == "minimax"]
        if entries:
            api_key = entries[0].runtime_api_key

    if not api_key:
        raise RuntimeError("No MINIMAX_API_KEY found")

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.2
    }).encode()

    req = urllib.request.Request(
        f"{MINIMAX_BASE_URL}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://hermes.local",
            "X-Title": "Hermes-Gera-Ingest"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Minimax HTTP {e.code}: {body[:200]}") from e


def extract_facts(conversation_text: str, existing_wiki: str = "") -> dict:
    """Extract structured facts from conversation using plain text parsing."""
    prompt = f"""Существующие wiki-факты:
{existing_wiki[:1500]}

---

Переписка:
{conversation_text[:3000]}

---

Твоя задача: извлеки из переписки НОВЫЕ факты, которых нет в существующей wiki.
Верни простой текст, каждую мысль на отдельной строке. Без JSON. Без markdown.

Ключевые факты:"""
    result = call_minimax(prompt)
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    # Parse: split by newlines, filter empty, clean up
    facts = []
    for line in content.split('\n'):
        line = line.strip()
        # Remove thinking tags and markdown
        line = re.sub(r'^【.*?】', '', line).strip()
        if line and len(line) > 10:
            facts.append(line)
    return {"facts": facts}


# ── File helpers ──────────────────────────────────────────────────────────────
def get_sessions():
    """List all session files, sorted."""
    if not SESSIONS_DIR.exists():
        return []
    return sorted([f for f in SESSIONS_DIR.glob("*.jsonl")])


def load_session(path: Path) -> list:
    """Load session messages from JSONL."""
    messages = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return messages


def format_conversation(messages: list) -> str:
    """Format messages as readable text."""
    lines = []
    for msg in messages:
        role = msg.get("role", "?")
        content = msg.get("content", "")
        ts = msg.get("timestamp", "")[:16]
        if content:
            prefix = "Денис" if role == "user" else "Гера"
            lines.append(f"[{ts}] {prefix}: {content[:500]}")
    return "\n".join(lines)


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"last_ingest": None, "ingested_sessions": []}


def save_manifest(m: dict):
    MANIFEST_PATH.write_text(json.dumps(m, indent=2, ensure_ascii=False))


def get_new_sessions(manifest: dict) -> list:
    """Get sessions to process."""
    all_sessions = get_sessions()
    ingested = set(manifest.get("ingested_sessions", []))
    new = [s for s in all_sessions if s.name not in ingested]
    # Filter: only 20260425 and 20260426
    new = [s for s in new if s.name >= "20260425" and s.name < "20260427"]
    return new


def get_existing_wiki_text() -> str:
    """Get all existing wiki content for context."""
    parts = []
    for md in WIKI_DIR.rglob("*.md"):
        if md.name.startswith("_") or md.name.startswith("."):
            continue
        try:
            parts.append(md.read_text(encoding="utf-8")[:500])
        except:
            pass
    return "\n---\n".join(parts)[:3000]


def write_session_facts(session_name: str, facts: list) -> bool:
    """Write extracted facts to a session file in projects/."""
    if not facts:
        return False
    projects_dir = WIKI_DIR / "projects"
    projects_dir.mkdir(exist_ok=True)
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", session_name.replace(".jsonl", ""))
    path = projects_dir / f"{safe_name}.md"
    lines = [
        f"# {session_name}",
        "",
        "## Извлечённые факты",
        ""
    ]
    for fact in facts:
        lines.append(f"- {fact}")
    content = "\n".join(lines) + "\n"
    # Append if exists
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        # Check for duplicates
        new_facts = [f for f in facts if f not in existing]
        if not new_facts:
            return False
        content = existing + "\n" + "\n".join([f"- {f}" for f in new_facts]) + "\n"
    path.write_text(content, encoding="utf-8")
    return True


def process_session(session_path: Path) -> bool:
    """Process a single session. Returns True if facts were written."""
    print(f"  Processing: {session_path.name}")
    messages = load_session(session_path)
    if len(messages) < 3:
        print(f"    Skipped: too few messages ({len(messages)})")
        return False
    text = format_conversation(messages)
    if len(text) < 150:
        print(f"    Skipped: conversation too short ({len(text)} chars)")
        return False
    try:
        existing = get_existing_wiki_text()
        result = extract_facts(text, existing)
    except Exception as e:
        print(f"    API Error: {e}")
        return False
    facts = result.get("facts", [])
    if not facts:
        print(f"    Skipped: no facts extracted")
        return False
    if write_session_facts(session_path.name, facts):
        print(f"    ✓ Wrote {len(facts)} facts to projects/")
        return True
    print(f"    No new facts (all duplicates)")
    return False


def main():
    manifest = load_manifest()
    sessions = get_new_sessions(manifest)
    total = len(sessions)
    print(f"Found {total} new sessions (Apr 25-26)")
    if total == 0:
        print("Nothing to do")
        return
    processed = 0
    for session_path in sessions:
        if process_session(session_path):
            processed += 1
            manifest["ingested_sessions"].append(session_path.name)
            manifest["last_ingest"] = session_path.name
            save_manifest(manifest)
        time.sleep(0.5)  # Rate limit
    print(f"\n✅ Done: {processed}/{total} sessions with new facts")


if __name__ == "__main__":
    main()
