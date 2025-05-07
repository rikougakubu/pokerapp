#!/usr/bin/env bash
set -euo pipefail
# --- nvm をロードして PATH に Node を追加 ---
export NVM_DIR="$HOME/.nvm"
# nvm.sh が無いときはエラーにしたくないので || true
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" || {
    echo "nvm.sh not found; npx も使えません" >&2
    exit 1
}

LOG_DIR="/home/kazu20040127/poker_app"
cd "$LOG_DIR"
echo "[start_app.sh] 開始: $(date)" >> cron_debug.log

# --- 既存プロセスを安全に kill ---
pkill -f streamlit      2>/dev/null || true
pkill -f localtunnel    2>/dev/null || true
sleep 1
rm -f lt_url.txt lt_pass.txt streamlit.log

# --- localtunnel (BG) ---
SUBDOMAIN="pokerapp-urip"
npx localtunnel --port 8501 --subdomain "$SUBDOMAIN" \
        > lt_url.txt 2>&1 &
LT_PID=$!

# --- Streamlit (前景=exec) ---
exec ~/.local/bin/streamlit run app.py --server.port 8501 \
        >> streamlit.log 2>&1
# ↑ exec にしたので、このシェルは Streamlit に置き換わる
#    ⇒ Streamlit が落ちた瞬間 EXIT trap が走る
