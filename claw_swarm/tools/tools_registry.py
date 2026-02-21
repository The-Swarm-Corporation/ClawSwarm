from claw_swarm.tools.claude_code_tool import (
    run_claude_agent,
    run_claude_agent_async,
    stream_claude_agent,
)
from claw_swarm.tools.launch_tokens import claim_fees, launch_token
from claw_swarm.tools.web_search import web_search

try:
    from swarms_tools import exa_search
except Exception:
    exa_search = None

tools = [
    claim_fees,
    launch_token,
    run_claude_agent,
    run_claude_agent_async,
    stream_claude_agent,
    web_search,
]

if exa_search is not None:
    tools.append(exa_search)
