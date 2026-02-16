"""
ClawSwarm main entrypoint: run the agent 24/7.

The agent polls the Messaging Gateway for Telegram, Discord, and WhatsApp messages,
processes each with the ClawSwarm Swarms agent (prompts in claw_swarm/prompts/),
and sends replies back. Run the gateway separately (python -m claw_swarm.gateway).

Usage:
  python -m claw_swarm.main

Or from the repo root:
  python -m claw_swarm.main

Env:
  GATEWAY_HOST, GATEWAY_PORT  - gateway address (default localhost:50051)
  AGENT_MODEL                  - Swarms agent model (default gpt-4o-mini)
  TELEGRAM_BOT_TOKEN, DISCORD_BOT_TOKEN, WHATSAPP_* - for sending replies
"""

from claw_swarm.agent_runner import main

if __name__ == "__main__":
    raise SystemExit(main())
