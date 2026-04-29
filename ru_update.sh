#!/bin/bash
# Hermes RU — Update Script
# Запускает полный цикл перевода одной командой
#
# Использование: ./ru_update.sh
#
# Цикл:
#   1. find_en_strings.py  — найти English строки
#   2. translate_llm.py     — перевести через LLM
#   3. apply_safe.py       — применить с бэкапом
#
# НЕ удаляет старые скрипты — они остаются рядом

set -e

echo "========================================"
echo "🔄 Hermes RU — Full Update Cycle"
echo "========================================"
echo ""

# Check MINIMAX_API_KEY
if [ -z "$MINIMAX_API_KEY" ]; then
    echo "⚠️  MINIMAX_API_KEY не установлен"
    echo "   Установи: export MINIMAX_API_KEY='твой_ключ'"
    echo "   Или добавь в ~/.hermes/.env"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📍 Рабочая директория: $SCRIPT_DIR"
echo ""

# Step 1: Find
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "① find_en_strings.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 find_en_strings.py
echo ""

# Step 2: Translate
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "② translate_llm.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 translate_llm.py
echo ""

# Step 3: Apply
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "③ apply_safe.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 apply_safe.py
echo ""

echo "========================================"
echo "✅ Цикл завершён!"
echo "========================================"
echo ""
echo "📋 Чтобы активировать переводы:"
echo "   hermes gateway restart"
echo ""
echo "📋 Чтобы откатить:"
echo "   ls backups/"
echo "   # скопируй нужный .bak и замени оригинал"
