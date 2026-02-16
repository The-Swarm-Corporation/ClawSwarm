#!/usr/bin/env bash
#
# Run the full ClawSwarm stack: Messaging Gateway + Agent (24/7).
# Exits on Ctrl+C or SIGTERM; both processes are stopped cleanly.
#
# Usage:
#   ./run.sh
#
# Prerequisites: set TELEGRAM_BOT_TOKEN, DISCORD_BOT_TOKEN, etc. (see README).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GATEWAY_PID=""
cleanup() {
  if [[ -n "$GATEWAY_PID" ]] && kill -0 "$GATEWAY_PID" 2>/dev/null; then
    echo "Stopping gateway (PID $GATEWAY_PID)..."
    kill "$GATEWAY_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" 2>/dev/null || true
  fi
  exit 0
}

trap cleanup SIGINT SIGTERM

echo "Starting Messaging Gateway..."
python -m claw_swarm.gateway &
GATEWAY_PID=$!

# Give the gateway a moment to bind
sleep 2

echo "Starting ClawSwarm Agent..."
python -m claw_swarm.main
