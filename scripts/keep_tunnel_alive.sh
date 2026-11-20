#!/usr/bin/env bash
# Resilient Auto-Healing Supervisor for Peer Cloudflare Tunnel
# Automatically restarts the tunnel if Cloudflare edge drops or reclaims the temporary session.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
URL_FILE="$PROJECT_ROOT/peer_tunnel_url.txt"
LOG_FILE="$PROJECT_ROOT/peer_tunnel.log"

echo "=== Starting DAT Practice Lab Peer Tunnel Supervisor ==="
echo "Monitoring target: http://localhost:5173"

cleanup() {
    echo "Stopping tunnel supervisor..."
    if [[ -n "${TUNNEL_PID:-}" ]]; then
        kill "$TUNNEL_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

while true; do
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Launching fresh Cloudflare tunnel..."
    /opt/homebrew/bin/cloudflared tunnel --url http://localhost:5173 > "$LOG_FILE" 2>&1 &
    TUNNEL_PID=$!

    # Wait for tunnel URL to appear in logs (up to 20 seconds)
    TUNNEL_URL=""
    for i in {1..20}; do
        sleep 1
        TUNNEL_URL=$(grep -o 'https://[-a-zA-Z0-9.]*\.trycloudflare\.com' "$LOG_FILE" | head -n 1 || true)
        if [[ -n "$TUNNEL_URL" ]]; then
            break
        fi
    done

    if [[ -n "$TUNNEL_URL" ]]; then
        echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Tunnel active: $TUNNEL_URL"
        echo "$TUNNEL_URL" > "$URL_FILE"
    else
        echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Warning: Could not detect tunnel URL in log."
    fi

    # Monitor loop: check if tunnel is alive and healthy
    FAIL_COUNT=0
    while kill -0 "$TUNNEL_PID" 2>/dev/null; do
        sleep 15
        
        # Check if the log contains the fatal "Unauthorized: Tunnel not found"
        if grep -q "Unauthorized: Tunnel not found" "$LOG_FILE" 2>/dev/null; then
            echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Cloudflare session expired on edge (Tunnel not found). Triggering auto-restart..."
            kill "$TUNNEL_PID" 2>/dev/null || true
            break
        fi

        # Health ping if URL is known
        if [[ -n "$TUNNEL_URL" ]]; then
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$TUNNEL_URL" || echo "000")
            if [[ "$HTTP_CODE" == "1016" || "$HTTP_CODE" == "530" || "$HTTP_CODE" == "000" ]]; then
                FAIL_COUNT=$((FAIL_COUNT + 1))
                echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Health check failed ($HTTP_CODE). Count: $FAIL_COUNT/3"
                if [[ $FAIL_COUNT -ge 3 ]]; then
                    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] 3 consecutive failures. Restarting tunnel..."
                    kill "$TUNNEL_PID" 2>/dev/null || true
                    break
                fi
            else
                FAIL_COUNT=0
            fi
        fi
    done

    wait "$TUNNEL_PID" 2>/dev/null || true
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Tunnel process stopped. Waiting 3s before auto-reconnect..."
    sleep 3
done
