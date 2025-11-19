#!/bin/bash
# Campaign Manager - Simple Setup

set -e

INSTALL_DIR="$HOME/.config/campaigno"
VENV_DIR="$INSTALL_DIR/venv"

echo "🚀 Campaign Manager Setup"
echo "📁 Installing to: $INSTALL_DIR"
echo

# 1. إنشاء venv
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ venv created"
else
    echo "✅ venv exists"
fi

# 2. تثبيت dependencies
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q rich pyyaml
echo "✅ Dependencies installed"

# 3. إنشاء wrapper للـTUI
cat > "$INSTALL_DIR/campaign-tui" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/campaign-tui.py" "$@"
EOF
chmod +x "$INSTALL_DIR/campaign-tui"
echo "✅ campaign-tui wrapper created"

# 4. إنشاء wrapper للـprompt
cat > "$INSTALL_DIR/campaign-prompt" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/campaign-prompt.py" "$@"
EOF
chmod +x "$INSTALL_DIR/campaign-prompt"
echo "✅ campaign-prompt wrapper created"

# 5. إضافة للـPATH
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "Add to your shell config (~/.bashrc or ~/.zshrc):"
echo
echo "# Campaign Manager"
echo "export PATH=\"$INSTALL_DIR:\$PATH\""
echo
echo "# Prompt integration (optional)"
echo "campaign_status() {"
echo "    $INSTALL_DIR/campaign-prompt 2>/dev/null || echo \"\""
echo "}"
echo "# For bash:"
echo "PS1=\"...\\\$(campaign_status)...\""
echo "# For zsh:"
echo "RPROMPT='\$(campaign_status)'"
echo
echo "Then run: campaign-tui init"
