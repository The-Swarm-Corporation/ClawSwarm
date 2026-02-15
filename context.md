Skip to content
kyegomez
swarms
Repository navigation
Code
Issues
55
 (55)
Pull requests
54
 (54)
Agents
Discussions
Actions
Projects
1
 (1)
Wiki
Security
5k+
 (5k+)
Insights
Settings
Owner avatar
swarms
Public
kyegomez/swarms
Go to file
t
Name		
kyegomez
kyegomez
Merge pull request #1364 from Steve-Dusty/debatewithjudge-fix
33eb024
 · 
17 hours ago
.github
Merge pull request #1254 from kyegomez/dependabot/github_actions/acti…
2 months ago
docs
[FEAT][Agent with selected tools method name] [Examples][Improve exam…
last week
examples
[FEAT][Agent with selected tools method name] [Examples][Improve exam…
last week
images
improve agent + marketplace integration docs
2 months ago
scripts
[Docs][Guide on how to enable agents to process images through base64]
2 weeks ago
swarms
Merge pull request #1364 from Steve-Dusty/debatewithjudge-fix
17 hours ago
tests
[Examples][for autosaving structures]
2 weeks ago
v9_examples
[FEAT][Bash tool for agent.auto] [Docs]
2 weeks ago
.env.example
[MIGRATION][Move InteractiveGroupchat -> Groupchat] [Examples Improve…
last month
.gitignore
[MIGRATION][Move InteractiveGroupchat -> Groupchat] [Examples Improve…
last month
CITATION.cff
Update CITATION.cff
8 months ago
CODE_OF_CONDUCT.md
[FIX][Email] [fix heavy swarm prompt]
4 months ago
CONTRIBUTING.md
[Improvement][HiearchicalSwarm] [Director reasoning improvement] [Imp…
3 months ago
LICENSE
debate multi agent orchestration docs
7 months ago
README.md
[README][New protocol support table updated] [Examples][new folder ch…
last month
SECURITY.md
[Docs][Voice agents single agent and multi-agent debate example with …
2 months ago
example.py
[Delete un-used files] [Agent][update max context length] [Improved CLI]
last month
example_autonomous_looper_run_bash.py
[FEAT][Agent with selected tools method name] [Examples][Improve exam…
last week
hiearchical_swarm_example.py
[Docs][Changes] Update HierarchicalSwarm documentation with missing p…
last month
pyproject.toml
Update ruff requirement from >=0.5.1,<0.14.15 to >=0.5.1,<0.15.1
last week
requirements.txt
added checks to conversation history
3 months ago
Repository files navigation
README
Code of conduct
Contributing
Apache-2.0 license
Security
Logo
The Enterprise-Grade Production-Ready Multi-Agent Orchestration Framework

🏠 Swarms Website   •   📙 Documentation   •   🛒 Swarms Marketplace

Version Downloads Twitter Discord

✨ Features
Swarms delivers a comprehensive, enterprise-grade multi-agent infrastructure platform designed for production-scale deployments and seamless integration with existing systems. Learn more about the swarms feature set here

Category	Features	Benefits
🏢 Enterprise Architecture	• Production-Ready Infrastructure
• High Availability Systems
• Modular Microservices Design
• Comprehensive Observability
• Backwards Compatibility	• 99.9%+ Uptime Guarantee
• Reduced Operational Overhead
• Seamless Legacy Integration
• Enhanced System Monitoring
• Risk-Free Migration Path
🤖 Multi-Agent Orchestration	• Hierarchical Agent Swarms
• Parallel Processing Pipelines
• Sequential Workflow Orchestration
• Graph-Based Agent Networks
• Dynamic Agent Composition
• Agent Registry Management	• Complex Business Process Automation
• Scalable Task Distribution
• Flexible Workflow Adaptation
• Optimized Resource Utilization
• Centralized Agent Governance
• Enterprise-Grade Agent Lifecycle Management
🔄 Enterprise Integration	• Multi-Model Provider Support
• Custom Agent Development Framework
• Extensive Enterprise Tool Library
• Multiple Memory Systems
• Backwards Compatibility with LangChain, AutoGen, CrewAI
• Standardized API Interfaces	• Vendor-Agnostic Architecture
• Custom Solution Development
• Extended Functionality Integration
• Enhanced Knowledge Management
• Seamless Framework Migration
• Reduced Integration Complexity
📈 Enterprise Scalability	• Concurrent Multi-Agent Processing
• Intelligent Resource Management
• Load Balancing & Auto-Scaling
• Horizontal Scaling Capabilities
• Performance Optimization
• Capacity Planning Tools	• High-Throughput Processing
• Cost-Effective Resource Utilization
• Elastic Scaling Based on Demand
• Linear Performance Scaling
• Optimized Response Times
• Predictable Growth Planning
🛠️ Developer Experience	• Intuitive Enterprise API
• Comprehensive Documentation
• Active Enterprise Community
• CLI & SDK Tools
• IDE Integration Support
• Code Generation Templates	• Accelerated Development Cycles
• Reduced Learning Curve
• Expert Community Support
• Rapid Deployment Capabilities
• Enhanced Developer Productivity
• Standardized Development Patterns
🔌 Supported Protocols & Integrations
Swarms seamlessly integrates with industry-standard protocols and open specifications, unlocking powerful capabilities for tool integration, payment processing, distributed agent orchestration, and model interoperability.

Protocol	Description	Use Cases	Documentation
MCP (Model Context Protocol)	Standardized protocol for AI agents to interact with external tools and services through MCP servers. Enables dynamic tool discovery and execution.	• Tool integration
• Multi-server connections
• External API access
• Database connectivity	MCP Integration Guide
X402	Cryptocurrency payment protocol for API endpoints. Enables monetization of agents with pay-per-use models.	• Agent monetization
• Payment gate protection
• Crypto payments
• Pay-per-use services	X402 Quickstart
AOP (Agent Orchestration Protocol)	Framework for deploying and managing agents as distributed services. Enables agent discovery, management, and execution through standardized protocols.	• Distributed agent deployment
• Agent discovery
• Service orchestration
• Scalable multi-agent systems	AOP Reference
Swarms Marketplace	Platform for discovering and sharing production-ready prompts, agents, and tools. Enables automatic prompt loading from the marketplace and publishing your own prompts directly from code.	• Prompt discovery and reuse
• One-line prompt loading
• Community prompt sharing
• Prompt monetization	Marketplace Tutorial
Open Responses	Open-source specification and ecosystem for multi-provider, interoperable LLM interfaces based on the OpenAI Responses API. Provides a unified schema and tooling for calling language models, streaming results, and composing agentic workflows—independent of provider.	• Unified LLM interfaces
• Streaming outputs
• Multi-provider orchestration
• Interoperable agent workflows	Open Responses Website
Agent Skills	Lightweight, markdown-based format for defining modular, reusable agent capabilities introduced by Anthropic. Enables specialization of agents without modifying code by loading skill definitions from simple SKILL.md files.	• Agent specialization
• Reusable skill libraries
• Code-free agent customization
• Claude Code compatibility	Agent Skills Documentation
Install 💻
Using pip
$ pip3 install -U swarms
Using uv (Recommended)
uv is a fast Python package installer and resolver, written in Rust.

$ uv pip install swarms
Using poetry
$ poetry add swarms
From source
# Clone the repository
$ git clone https://github.com/kyegomez/swarms.git
$ cd swarms
$ pip install -r requirements.txt
Environment Configuration
Learn more about the environment configuration here

OPENAI_API_KEY=""
WORKSPACE_DIR="agent_workspace"
ANTHROPIC_API_KEY=""
GROQ_API_KEY=""
🤖 Your First Agent
An Agent is the fundamental building block of a swarm—an autonomous entity powered by an LLM + Tools + Memory. Learn more Here

from swarms import Agent

# Initialize a new agent
agent = Agent(
    model_name="gpt-4o-mini", # Specify the LLM
    max_loops="auto",              # Set the number of interactions
    interactive=True,         # Enable interactive mode for real-time feedback
)

# Run the agent with a task
agent.run("What are the key benefits of using a multi-agent system?")
🤝 Your First Swarm: Multi-Agent Collaboration
A Swarm consists of multiple agents working together. This simple example creates a two-agent workflow for researching and writing a blog post. Learn More About SequentialWorkflow

from swarms import Agent, SequentialWorkflow

# Agent 1: The Researcher
researcher = Agent(
    agent_name="Researcher",
    system_prompt="Your job is to research the provided topic and provide a detailed summary.",
    model_name="gpt-4o-mini",
)

# Agent 2: The Writer
writer = Agent(
    agent_name="Writer",
    system_prompt="Your job is to take the research summary and write a beautiful, engaging blog post about it.",
    model_name="gpt-4o-mini",
)

# Create a sequential workflow where the researcher's output feeds into the writer's input
workflow = SequentialWorkflow(agents=[researcher, writer])

# Run the workflow on a task
final_post = workflow.run("The history and future of artificial intelligence")
print(final_post)
🤖 AutoSwarmBuilder: Autonomous Agent Generation
The AutoSwarmBuilder automatically generates specialized agents and their workflows based on your task description. Simply describe what you need, and it will create a complete multi-agent system with detailed prompts and optimal agent configurations. Learn more about AutoSwarmBuilder

from swarms.structs.auto_swarm_builder import AutoSwarmBuilder
import json

# Initialize the AutoSwarmBuilder
swarm = AutoSwarmBuilder(
    name="My Swarm",
    description="A swarm of agents",
    verbose=True,
    max_loops=1,
    return_agents=True,
    model_name="gpt-4o-mini",
)

# Let the builder automatically create agents and workflows
result = swarm.run(
    task="Create an accounting team to analyze crypto transactions, "
         "there must be 5 agents in the team with extremely extensive prompts. "
         "Make the prompts extremely detailed and specific and long and comprehensive. "
         "Make sure to include all the details of the task in the prompts."
)

# The result contains the generated agents and their configurations
print(json.dumps(result, indent=4))
The AutoSwarmBuilder provides:

Automatic Agent Generation: Creates specialized agents based on task requirements
Intelligent Prompt Engineering: Generates comprehensive, detailed prompts for each agent
Optimal Workflow Design: Determines the best agent interactions and workflow structure
Production-Ready Configurations: Returns fully configured agents ready for deployment
Flexible Architecture: Supports various swarm types and agent specializations
This feature is perfect for rapid prototyping, complex task decomposition, and creating specialized agent teams without manual configuration.

🏗️ Available Multi-Agent Architectures
swarms provides a variety of powerful, pre-built multi-agent architectures enabling you to orchestrate agents in various ways. Choose the right structure for your specific problem to build efficient and reliable production systems.

Architecture	Description	Best For
SequentialWorkflow	Agents execute tasks in a linear chain; the output of one agent becomes the input for the next.	Step-by-step processes such as data transformation pipelines and report generation.
ConcurrentWorkflow	Agents run tasks simultaneously for maximum efficiency.	High-throughput tasks such as batch processing and parallel data analysis.
AgentRearrange	Dynamically maps complex relationships (e.g., a -> b, c) between agents.	Flexible and adaptive workflows, task distribution, and dynamic routing.
GraphWorkflow	Orchestrates agents as nodes in a Directed Acyclic Graph (DAG).	Complex projects with intricate dependencies, such as software builds.
MixtureOfAgents (MoA)	Utilizes multiple expert agents in parallel and synthesizes their outputs.	Complex problem-solving and achieving state-of-the-art performance through collaboration.
GroupChat	Agents collaborate and make decisions through a conversational interface.	Real-time collaborative decision-making, negotiations, and brainstorming.
ForestSwarm	Dynamically selects the most suitable agent or tree of agents for a given task.	Task routing, optimizing for expertise, and complex decision-making trees.
HierarchicalSwarm	Orchestrates agents with a director who creates plans and distributes tasks to specialized worker agents.	Complex project management, team coordination, and hierarchical decision-making with feedback loops.
HeavySwarm	Implements a five-phase workflow with specialized agents (Research, Analysis, Alternatives, Verification) for comprehensive task analysis.	Complex research and analysis tasks, financial analysis, strategic planning, and comprehensive reporting.
SwarmRouter	A universal orchestrator that provides a single interface to run any type of swarm with dynamic selection.	Simplifying complex workflows, switching between swarm strategies, and unified multi-agent management.
SequentialWorkflow
A SequentialWorkflow executes tasks in a strict order, forming a pipeline where each agent builds upon the work of the previous one. SequentialWorkflow is Ideal for processes that have clear, ordered steps. This ensures that tasks with dependencies are handled correctly.

from swarms import Agent, SequentialWorkflow

# Agent 1: The Researcher
researcher = Agent(
    agent_name="Researcher",
    system_prompt="Your job is to research the provided topic and provide a detailed summary.",
    model_name="gpt-4o-mini",
)

# Agent 2: The Writer
writer = Agent(
    agent_name="Writer",
    system_prompt="Your job is to take the research summary and write a beautiful, engaging blog post about it.",
    model_name="gpt-4o-mini",
)

# Create a sequential workflow where the researcher's output feeds into the writer's input
workflow = SequentialWorkflow(agents=[researcher, writer])

# Run the workflow on a task
final_post = workflow.run("The history and future of artificial intelligence")
print(final_post)
ConcurrentWorkflow
A ConcurrentWorkflow runs multiple agents simultaneously, allowing for parallel execution of tasks. This architecture drastically reduces execution time for tasks that can be performed in parallel, making it ideal for high-throughput scenarios where agents work on similar tasks concurrently.

from swarms import Agent, ConcurrentWorkflow

# Create agents for different analysis tasks
market_analyst = Agent(
    agent_name="Market-Analyst",
    system_prompt="Analyze market trends and provide insights on the given topic.",
    model_name="gpt-4o-mini",
    max_loops=1,
)

financial_analyst = Agent(
    agent_name="Financial-Analyst", 
    system_prompt="Provide financial analysis and recommendations on the given topic.",
    model_name="gpt-4o-mini",
    max_loops=1,
)

risk_analyst = Agent(
    agent_name="Risk-Analyst",
    system_prompt="Assess risks and provide risk management strategies for the given topic.",
    model_name="gpt-4o-mini", 
    max_loops=1,
)

# Create concurrent workflow
concurrent_workflow = ConcurrentWorkflow(
    agents=[market_analyst, financial_analyst, risk_analyst],
    max_loops=1,
)

# Run all agents concurrently on the same task
results = concurrent_workflow.run(
    "Analyze the potential impact of AI technology on the healthcare industry"
)

print(results)
AgentRearrange
Inspired by einsum, AgentRearrange lets you define complex, non-linear relationships between agents using a simple string-based syntax. Learn more. This architecture is perfect for orchestrating dynamic workflows where agents might work in parallel, in sequence, or in any combination you choose.

from swarms import Agent, AgentRearrange

# Define agents
researcher = Agent(agent_name="researcher", model_name="gpt-4o-mini")
writer = Agent(agent_name="writer", model_name="gpt-4o-mini")
editor = Agent(agent_name="editor", model_name="gpt-4o-mini")

# Define a flow: researcher sends work to both writer and editor simultaneously
# This is a one-to-many relationship
flow = "researcher -> writer, editor"

# Create the rearrangement system
rearrange_system = AgentRearrange(
    agents=[researcher, writer, editor],
    flow=flow,
)

# Run the swarm
outputs = rearrange_system.run("Analyze the impact of AI on modern cinema.")
print(outputs)
SwarmRouter: The Universal Swarm Orchestrator
The SwarmRouter simplifies building complex workflows by providing a single interface to run any type of swarm. Instead of importing and managing different swarm classes, you can dynamically select the one you need just by changing the swarm_type parameter. Read the full documentation

This makes your code cleaner and more flexible, allowing you to switch between different multi-agent strategies with ease. Here's a complete example that shows how to define agents and then use SwarmRouter to execute the same task using different collaborative strategies.

from swarms import Agent
from swarms.structs.swarm_router import SwarmRouter, SwarmType

# Define a few generic agents
writer = Agent(agent_name="Writer", system_prompt="You are a creative writer.", model_name="gpt-4o-mini")
editor = Agent(agent_name="Editor", system_prompt="You are an expert editor for stories.", model_name="gpt-4o-mini")
reviewer = Agent(agent_name="Reviewer", system_prompt="You are a final reviewer who gives a score.", model_name="gpt-4o-mini")

# The agents and task will be the same for all examples
agents = [writer, editor, reviewer]
task = "Write a short story about a robot who discovers music."

# --- Example 1: SequentialWorkflow ---
# Agents run one after another in a chain: Writer -> Editor -> Reviewer.
print("Running a Sequential Workflow...")
sequential_router = SwarmRouter(swarm_type=SwarmType.SequentialWorkflow, agents=agents)
sequential_output = sequential_router.run(task)
print(f"Final Sequential Output:\n{sequential_output}\n")

# --- Example 2: ConcurrentWorkflow ---
# All agents receive the same initial task and run at the same time.
print("Running a Concurrent Workflow...")
concurrent_router = SwarmRouter(swarm_type=SwarmType.ConcurrentWorkflow, agents=agents)
concurrent_outputs = concurrent_router.run(task)
# This returns a dictionary of each agent's output
for agent_name, output in concurrent_outputs.items():
    print(f"Output from {agent_name}:\n{output}\n")

# --- Example 3: MixtureOfAgents ---
# All agents run in parallel, and a special 'aggregator' agent synthesizes their outputs.
print("Running a Mixture of Agents Workflow...")
aggregator = Agent(
    agent_name="Aggregator",
    system_prompt="Combine the story, edits, and review into a final document.",
    model_name="gpt-4o-mini"
)
moa_router = SwarmRouter(
    swarm_type=SwarmType.MixtureOfAgents,
    agents=agents,
    aggregator_agent=aggregator, # MoA requires an aggregator
)
aggregated_output = moa_router.run(task)
print(f"Final Aggregated Output:\n{aggregated_output}\n")
The SwarmRouter is a powerful tool for simplifying multi-agent orchestration. It provides a consistent and flexible way to deploy different collaborative strategies, allowing you to build more sophisticated applications with less code.

MixtureOfAgents (MoA)
The MixtureOfAgents architecture processes tasks by feeding them to multiple "expert" agents in parallel. Their diverse outputs are then synthesized by an aggregator agent to produce a final, high-quality result. Learn more here

from swarms import Agent, MixtureOfAgents

# Define expert agents
financial_analyst = Agent(agent_name="FinancialAnalyst", system_prompt="Analyze financial data.", model_name="gpt-4o-mini")
market_analyst = Agent(agent_name="MarketAnalyst", system_prompt="Analyze market trends.", model_name="gpt-4o-mini")
risk_analyst = Agent(agent_name="RiskAnalyst", system_prompt="Analyze investment risks.", model_name="gpt-4o-mini")

# Define the aggregator agent
aggregator = Agent(
    agent_name="InvestmentAdvisor",
    system_prompt="Synthesize the financial, market, and risk analyses to provide a final investment recommendation.",
    model_name="gpt-4o-mini"
)

# Create the MoA swarm
moa_swarm = MixtureOfAgents(
    agents=[financial_analyst, market_analyst, risk_analyst],
    aggregator_agent=aggregator,
)

# Run the swarm
recommendation = moa_swarm.run("Should we invest in NVIDIA stock right now?")
print(recommendation)
GroupChat
GroupChat creates a conversational environment where multiple agents can interact, discuss, and collaboratively solve a problem. You can define the speaking order or let it be determined dynamically. This architecture is ideal for tasks that benefit from debate and multi-perspective reasoning, such as contract negotiation, brainstorming, or complex decision-making.

from swarms import Agent, GroupChat

# Define agents for a debate
tech_optimist = Agent(agent_name="TechOptimist", system_prompt="Argue for the benefits of AI in society.", model_name="gpt-4o-mini")
tech_critic = Agent(agent_name="TechCritic", system_prompt="Argue against the unchecked advancement of AI.", model_name="gpt-4o-mini")

# Create the group chat
chat = GroupChat(
    agents=[tech_optimist, tech_critic],
    max_loops=4, # Limit the number of turns in the conversation
)

# Run the chat with an initial topic
conversation_history = chat.run(
    "Let's discuss the societal impact of artificial intelligence."
)

# Print the full conversation
for message in conversation_history:
    print(f"[{message['agent_name']}]: {message['content']}")
HierarchicalSwarm
HierarchicalSwarm implements a director-worker pattern where a central director agent creates comprehensive plans and distributes specific tasks to specialized worker agents. The director evaluates results and can issue new orders in feedback loops, making it ideal for complex project management and team coordination scenarios.

from swarms import Agent, HierarchicalSwarm

# Define specialized worker agents
content_strategist = Agent(
    agent_name="Content-Strategist",
    system_prompt="You are a senior content strategist. Develop comprehensive content strategies, editorial calendars, and content roadmaps.",
    model_name="gpt-4o-mini"
)

creative_director = Agent(
    agent_name="Creative-Director", 
    system_prompt="You are a creative director. Develop compelling advertising concepts, visual directions, and campaign creativity.",
    model_name="gpt-4o-mini"
)

seo_specialist = Agent(
    agent_name="SEO-Specialist",
    system_prompt="You are an SEO expert. Conduct keyword research, optimize content, and develop organic growth strategies.",
    model_name="gpt-4o-mini"
)

brand_strategist = Agent(
    agent_name="Brand-Strategist",
    system_prompt="You are a brand strategist. Develop brand positioning, identity systems, and market differentiation strategies.",
    model_name="gpt-4o-mini"
)

# Create the hierarchical swarm with a director
marketing_swarm = HierarchicalSwarm(
    name="Marketing-Team-Swarm",
    description="A comprehensive marketing team with specialized agents coordinated by a director",
    agents=[content_strategist, creative_director, seo_specialist, brand_strategist],
    max_loops=2,  # Allow for feedback and refinement
    verbose=True
)

# Run the swarm on a complex marketing challenge
result = marketing_swarm.run(
    "Develop a comprehensive marketing strategy for a new SaaS product launch. "
    "The product is a project management tool targeting small to medium businesses. "
    "Coordinate the team to create content strategy, creative campaigns, SEO optimization, "
    "and brand positioning that work together cohesively."
)

print(result)
The HierarchicalSwarm excels at:

Complex Project Management: Breaking down large tasks into specialized subtasks
Team Coordination: Ensuring all agents work toward unified goals
Quality Control: Director provides feedback and refinement loops
Scalable Workflows: Easy to add new specialized agents as needed
HeavySwarm
HeavySwarm implements a sophisticated 5-phase workflow inspired by X.AI's Grok heavy implementation. It uses specialized agents (Research, Analysis, Alternatives, Verification) to provide comprehensive task analysis through intelligent question generation, parallel execution, and synthesis. This architecture excels at complex research and analysis tasks requiring thorough investigation and multiple perspectives.

from swarms import HeavySwarm

# Pip install swarms-tools
from swarms_tools import exa_search

swarm = HeavySwarm(
    name="Gold ETF Research Team",
    description="A team of agents that research the best gold ETFs",
    worker_model_name="claude-sonnet-4-20250514",
    show_dashboard=True,
    question_agent_model_name="gpt-4.1",
    loops_per_agent=1,
    agent_prints_on=False,
    worker_tools=[exa_search],
    random_loops_per_agent=True,
)

prompt = (
    "Find the best 3 gold ETFs. For each ETF, provide the ticker symbol, "
    "full name, current price, expense ratio, assets under management, and "
    "a brief explanation of why it is considered among the best. Present the information "
    "in a clear, structured format suitable for investors. Scrape the data from the web. "
)

out = swarm.run(prompt)
print(out)
The HeavySwarm provides:

5-Phase Analysis: Question generation, research, analysis, alternatives, and verification

Specialized Agents: Each phase uses purpose-built agents for optimal results

Comprehensive Coverage: Multiple perspectives and thorough investigation

Real-time Dashboard: Optional visualization of the analysis process

Structured Output: Well-organized and actionable results

This architecture is perfect for financial analysis, strategic planning, research reports, and any task requiring deep, multi-faceted analysis. Learn more about HeavySwarm

Social Algorithms
Social Algorithms provide a flexible framework for defining custom communication patterns between agents. You can upload any arbitrary social algorithm as a callable that defines the sequence of communication, enabling agents to talk to each other in sophisticated ways. Learn more about Social Algorithms

from swarms import Agent, SocialAlgorithms

# Define a custom social algorithm
def research_analysis_synthesis_algorithm(agents, task, **kwargs):
    # Agent 1 researches the topic
    research_result = agents[0].run(f"Research: {task}")
    
    # Agent 2 analyzes the research
    analysis = agents[1].run(f"Analyze this research: {research_result}")
    
    # Agent 3 synthesizes the findings
    synthesis = agents[2].run(f"Synthesize: {research_result} + {analysis}")
    
    return {
        "research": research_result,
        "analysis": analysis,
        "synthesis": synthesis
    }

# Create agents
researcher = Agent(
  agent_name="Researcher",
  agent_description="Expert in comprehensive research and information gathering.",
  model_name="gpt-4.1"
)
analyst = Agent(
  agent_name="Analyst",
  agent_description="Specialist in analyzing and interpreting data.",
  model_name="gpt-4.1"
)
synthesizer = Agent(
  agent_name="Synthesizer",
  agent_description="Focused on synthesizing and integrating research insights.",
  model_name="gpt-4.1"
)

# Create social algorithm
social_alg = SocialAlgorithms(
    name="Research-Analysis-Synthesis",
    agents=[researcher, analyst, synthesizer],
    social_algorithm=research_analysis_synthesis_algorithm,
    verbose=True
)

# Run the algorithm
result = social_alg.run("The impact of AI on healthcare")
print(result.final_outputs)
Perfect for implementing complex multi-agent workflows, collaborative problem-solving, and custom communication protocols.

Agent Orchestration Protocol (AOP)
The Agent Orchestration Protocol (AOP) is a powerful framework for deploying and managing agents as distributed services. AOP enables agents to be discovered, managed, and executed through a standardized protocol, making it perfect for building scalable multi-agent systems. Learn more about AOP

from swarms import Agent
from swarms.structs.aop import AOP

# Create specialized agents
research_agent = Agent(
    agent_name="Research-Agent",
    agent_description="Expert in research and data collection",
    model_name="anthropic/claude-sonnet-4-5",
    max_loops=1,
    tags=["research", "data-collection", "analysis"],
    capabilities=["web-search", "data-gathering", "report-generation"],
    role="researcher"
)

analysis_agent = Agent(
    agent_name="Analysis-Agent", 
    agent_description="Expert in data analysis and insights",
    model_name="anthropic/claude-sonnet-4-5",
    max_loops=1,
    tags=["analysis", "data-processing", "insights"],
    capabilities=["statistical-analysis", "pattern-recognition", "visualization"],
    role="analyst"
)

# Create AOP server
deployer = AOP(
    server_name="ResearchCluster",
    port=8000,
    verbose=True
)

# Add agents to the server
deployer.add_agent(
    agent=research_agent,
    tool_name="research_tool",
    tool_description="Research and data collection tool",
    timeout=30,
    max_retries=3
)

deployer.add_agent(
    agent=analysis_agent,
    tool_name="analysis_tool", 
    tool_description="Data analysis and insights tool",
    timeout=30,
    max_retries=3
)

# List all registered agents
print("Registered agents:", deployer.list_agents())

# Start the AOP server
deployer.run()
Perfect for deploying large scale multi-agent systems. Read the complete AOP documentation

Documentation
Documentation is located here at: docs.swarms.world

Examples
Explore comprehensive examples and tutorials to learn how to use Swarms effectively.

Category	Example	Description	Link
Basic Examples	Basic Agent	Simple agent setup and usage	Basic Agent
Basic Examples	Agent with Tools	Using agents with various tools	Agent with Tools
Basic Examples	Agent with Structured Outputs	Working with structured data outputs	Structured Outputs
Basic Examples	Agent with MCP Integration	Model Context Protocol integration	MCP Integration
Basic Examples	Vision Processing	Agents with image processing capabilities	Vision Processing
Basic Examples	Multiple Images	Working with multiple images	Multiple Images
Basic Examples	Vision and Tools	Combining vision with tool usage	Vision and Tools
Basic Examples	Agent Streaming	Real-time agent output streaming	Agent Streaming
Basic Examples	Agent Output Types	Different output formats and types	Output Types
Basic Examples	Gradio Chat Interface	Building interactive chat interfaces	Gradio UI
Model Providers	Model Providers Overview	Complete guide to supported models	Model Providers
Model Providers	OpenAI	OpenAI model integration	OpenAI Examples
Model Providers	Anthropic	Claude model integration	Anthropic Examples
Model Providers	Groq	Groq model integration	Groq Examples
Model Providers	Cohere	Cohere model integration	Cohere Examples
Model Providers	DeepSeek	DeepSeek model integration	DeepSeek Examples
Model Providers	Ollama	Local Ollama model integration	Ollama Examples
Model Providers	OpenRouter	OpenRouter model integration	OpenRouter Examples
Model Providers	XAI	XAI model integration	XAI Examples
Model Providers	Llama4	Llama4 model integration	Llama4 Examples
Multi-Agent Architecture	HierarchicalSwarm	Hierarchical agent orchestration	HierarchicalSwarm Examples
Multi-Agent Architecture	Hybrid Hierarchical-Cluster Swarm	Advanced hierarchical patterns	HHCS Examples
Multi-Agent Architecture	GroupChat	Multi-agent conversations	GroupChat Examples
Multi-Agent Architecture	Sequential Workflow	Step-by-step agent workflows	Sequential Examples
Multi-Agent Architecture	SwarmRouter	Universal swarm orchestration	SwarmRouter Examples
Multi-Agent Architecture	MultiAgentRouter	Minimal router example	MultiAgentRouter Examples
Multi-Agent Architecture	ConcurrentWorkflow	Parallel agent execution	Concurrent Examples
Multi-Agent Architecture	Mixture of Agents	Expert agent collaboration	MoA Examples
Multi-Agent Architecture	Unique Swarms	Specialized swarm patterns	Unique Swarms
Multi-Agent Architecture	Agents as Tools	Using agents as tools in workflows	Agents as Tools
Multi-Agent Architecture	Aggregate Responses	Combining multiple agent outputs	Aggregate Examples
Multi-Agent Architecture	Interactive GroupChat	Real-time agent interactions	Interactive GroupChat
Deployment Solutions	Agent Orchestration Protocol (AOP)	Deploy agents as distributed services with discovery and management	AOP Reference
Applications	Advanced Research System	Multi-agent research system inspired by Anthropic's research methodology	AdvancedResearch
Applications	Hospital Simulation	Healthcare simulation system using multi-agent architecture	HospitalSim
Applications	Browser Agents	Web automation with agents	Browser Agents
Applications	Medical Analysis	Healthcare applications	Medical Examples
Applications	Finance Analysis	Financial applications	Finance Examples
Cookbook & Templates	Examples Overview	Complete examples directory	Examples Index
Cookbook & Templates	Cookbook Index	Curated example collection	Cookbook
Cookbook & Templates	Paper Implementations	Research paper implementations	Paper Implementations
Cookbook & Templates	Templates & Applications	Reusable templates	Templates
Contribute to Swarms
Our mission is to accelerate the transition to a fully autonomous world economy by providing enterprise-grade, production-ready infrastructure that enables seamless deployment and orchestration of millions of autonomous agents. We are creating the operating system for the agent economy, and we need your help to achieve this goal.

Swarms is built by the community, for the community. We believe that collaborative development is the key to pushing the boundaries of what's possible with multi-agent AI. Your contributions are not only welcome—they are essential to our mission. Learn more about why you should contribute to Swarms

Why Contribute?
By joining us, you have the opportunity to:

Work on the Frontier of Agents: Shape the future of autonomous agent technology and help build a production-grade, open-source framework.

Join a Vibrant Community: Collaborate with a passionate and growing group of agent developers, researchers, and agent enthusasits.

Make a Tangible Impact: Whether you're fixing a bug, adding a new feature, or improving documentation, your work will be used in real-world applications.

Learn and Grow: Gain hands-on experience with advanced AI concepts and strengthen your software engineering skills.

Discover more about our mission and the benefits of becoming a contributor in our official Contributor's Guide.

How to Get Started
We've made it easy to start contributing. Here's how you can help:

Find an Issue to Tackle: The best way to begin is by visiting our contributing project board. Look for issues tagged with good first issue—these are specifically selected for new contributors.

Report a Bug or Request a Feature: Have a new idea or found something that isn't working right? We'd love to hear from you. Please file a Bug Report or Feature Request on our GitHub Issues page.

Understand Our Workflow and Standards: Before submitting your work, please review our complete Contribution Guidelines. To help maintain code quality, we also encourage you to read our guide on Code Cleanliness.

Join the Discussion: To participate in roadmap discussions and connect with other developers, join our community on Discord.

✨ Thank You to Our Contributors
Thank you for contributing to swarms. Your work is extremely appreciated and recognized.


🙏 Thank You to Our Community
We're incredibly grateful to everyone who supports Swarms! Your stars, forks, and contributions help make this project better every day.

Forkers repo roster for @kyegomez/swarms

Stargazers repo roster for @kyegomez/swarms

Join the Swarms community 👾👾👾
Join our community of agent engineers and researchers for technical support, cutting-edge updates, and exclusive access to world-class agent engineering insights!

Platform	Description	Link
📚 Documentation	Official documentation and guides	docs.swarms.world
📝 Blog	Latest updates and technical articles	Medium
💬 Discord	Live chat and community support	Join Discord
🐦 Twitter	Latest news and announcements	@swarms_corp
👥 LinkedIn	Professional network and updates	The Swarm Corporation
📺 YouTube	Tutorials and demos	Swarms Channel
🎫 Events	Join our community events	Sign up here
🚀 Onboarding Session	Get onboarded with Kye Gomez, creator and lead maintainer of Swarms	Book Session
Citation
If you use swarms in your research, please cite the project by referencing the metadata in CITATION.cff.

@misc{SWARMS_2022,
  author  = {Kye Gomez and Pliny and Zack Bradshaw and Ilumn and Harshal and the Swarms Community},
  title   = {{Swarms: Production-Grade Multi-Agent Infrastructure Platform}},
  year    = {2022},
  howpublished = {\url{https://github.com/kyegomez/swarms}},
  note    = {Documentation available at \url{https://docs.swarms.world}},
  version = {latest}
License
Swarms is licensed under the Apache License 2.0. Learn more here

About
The Enterprise-Grade Production-Ready Multi-Agent Orchestration Framework. Website: https://swarms.ai

docs.swarms.world
Topics
machine-learning ai artificial-intelligence prompt-toolkit swarms agents multi-agent-systems huggingface gpt4 prompt-engineering prompting chatgpt langchain gpt4all langchain-python tree-of-thoughts agentic-workflow agentic-ai
Resources
 Readme
License
 Apache-2.0 license
Code of conduct
 Code of conduct
Contributing
 Contributing
Security policy
 Security policy
Citation
 Activity
Stars
 5.8k stars
Watchers
 61 watching
Forks
 735 forks
Releases 140
6.8.1
Latest
on Dec 27, 2024
+ 139 releases
Sponsor this project
@kyegomez
kyegomez Kye Gomez
Learn more about GitHub Sponsors
Packages
1
swarms
Used by 421
@thebyte007
@Evogoatml
@secureonelabs
@GlacierEQ
@nikivdev
@SirBoely
@CrazyDubya
@khalilsnoussi
+ 413
Contributors
43
@kyegomez
@dependabot[bot]
@elder-plinius
@IlumCI
@Wyatt-Stanke
@harshalmore31
@sambhavnoobcoder
@ZackBradshaw
@aparekh02
@hughiwnl
@Steve-Dusty
@Occupying-Mars
@GoldenWind8
@vyomakesh09
+ 29 contributors
Languages
Python
99.6%
 
Other
0.4%
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information


Swarms Tools¶
Welcome to Swarms Tools, the ultimate package for integrating cutting-edge APIs into Python functions with seamless multi-agent system compatibility. Designed for enterprises at the forefront of innovation, Swarms Tools is your key to simplifying complexity and unlocking operational excellence.

🚀 Features¶
Unified API Integration: Ready-to-use Python functions for financial data, social media, IoT, and more.
Enterprise-Grade Design: Comprehensive type hints, structured outputs, and robust documentation.
Agent-Ready Framework: Optimized for seamless integration into Swarms' multi-agent orchestration systems.
Expandable Architecture: Easily extend functionality with a standardized schema for new tools.
🔧 Installation¶

pip3 install -U swarms-tools
📂 Directory Structure¶

swarms-tools/
├── swarms_tools/
│   ├── finance/
│   │   ├── htx_tool.py
│   │   ├── eodh_api.py
│   │   └── coingecko_tool.py
│   ├── social_media/
│   │   ├── telegram_tool.py
│   ├── utilities/
│   │   └── logging.py
├── tests/
│   ├── test_financial_data.py
│   └── test_social_media.py
└── README.md
💼 Use Cases¶
Finance¶
Explore our diverse range of financial tools, designed to streamline your operations. If you need a tool not listed, feel free to submit an issue or accelerate integration by contributing a pull request with your tool of choice.

Tool Name	Function	Description
fetch_stock_news	fetch_stock_news	Fetches the latest stock news and updates.
fetch_htx_data	fetch_htx_data	Retrieves financial data from the HTX platform.
yahoo_finance_api	yahoo_finance_api	Fetches comprehensive stock data from Yahoo Finance, including prices and trends.
coin_gecko_coin_api	coin_gecko_coin_api	Fetches cryptocurrency data from CoinGecko, including market and price information.
helius_api_tool	helius_api_tool	Retrieves blockchain account, transaction, or token data using the Helius API.
okx_api_tool	okx_api_tool	Fetches detailed cryptocurrency data for coins from the OKX exchange.
Financial Data Retrieval¶
Enable precise and actionable financial insights:

Example 1: Fetch Historical Data¶

from swarms_tools import fetch_htx_data

# Fetch historical trading data for "Swarms Corporation"
response = fetch_htx_data("swarms")
print(response)
Example 2: Stock News Analysis¶

from swarms_tools import fetch_stock_news

# Retrieve latest stock news for Apple
news = fetch_stock_news("AAPL")
print(news)
Example 3: Cryptocurrency Metrics¶

from swarms_tools import coin_gecko_coin_api

# Fetch live data for Bitcoin
crypto_data = coin_gecko_coin_api("bitcoin")
print(crypto_data)
Social Media Automation¶
Streamline communication and engagement:

Example: Telegram Bot Messaging¶

from swarms_tools import telegram_dm_or_tag_api

def send_alert(response: str):
    telegram_dm_or_tag_api(response)

# Send a message to a user or group
send_alert("Mission-critical update from Swarms.")
Dex Screener¶
This is a tool that allows you to fetch data from the Dex Screener API. It supports multiple chains and multiple tokens.


from swarms_tools.finance.dex_screener import (
    fetch_latest_token_boosts,
    fetch_dex_screener_profiles,
)


fetch_dex_screener_profiles()
fetch_latest_token_boosts()
Structs¶
The tool chainer enables the execution of multiple tools in a sequence, allowing for the aggregation of their results in either a parallel or sequential manner.


# Example usage
from loguru import logger

from swarms_tools.structs import tool_chainer


if __name__ == "__main__":
    logger.add("tool_chainer.log", rotation="500 MB", level="INFO")

    # Example tools
    def tool1():
        return "Tool1 Result"

    def tool2():
        return "Tool2 Result"

    # def tool3():
    #     raise ValueError("Simulated error in Tool3")

    tools = [tool1, tool2]

    # Parallel execution
    parallel_results = tool_chainer(tools, parallel=True)
    print("Parallel Results:", parallel_results)

    # Sequential execution
    # sequential_results = tool_chainer(tools, parallel=False)
    # print("Sequential Results:", sequential_results)
¶
🧩 Standardized Schema¶
Every tool in Swarms Tools adheres to a strict schema for maintainability and interoperability:

Schema Template¶
Functionality:
Encapsulate API logic into a modular, reusable function.

Typing:

Leverage Python type hints for input validation and clarity.
Example:


def fetch_data(symbol: str, date_range: str) -> str:
    """
    Fetch financial data for a given symbol and date range.

    Args:
        symbol (str): Ticker symbol of the asset.
        date_range (str): Timeframe for the data (e.g., '1d', '1m', '1y').

    Returns:
        dict: A dictionary containing financial metrics.
    """
    pass
Documentation:
Include detailed docstrings with parameter explanations and usage examples.

Output Standardization:

Ensure consistent outputs (e.g., strings) for easy downstream agent integration.

API-Key Management:

All API keys must be fetched with os.getenv("YOUR_KEY")
📖 Documentation¶
Comprehensive documentation is available to guide developers and enterprises. Visit our official docs for detailed API references, usage examples, and best practices.

🛠 Contributing¶
We welcome contributions from the global developer community. To contribute:

Fork the Repository: Start by forking the repository.
Create a Feature Branch: Use a descriptive branch name: feature/add-new-tool.
Commit Your Changes: Write meaningful commit messages.
Submit a Pull Request: Open a pull request for review.
🛡️ License¶
This project is licensed under the MIT License. See the LICENSE file for details.

🌠 Join the Future¶
Explore the limitless possibilities of agent-based systems. Together, we can build a smarter, faster, and more interconnected world.

Visit us: Swarms Corporation
Follow us: Twitter

Swarms Tools Documentation¶
Swarms provides a comprehensive toolkit for integrating various types of tools into your AI agents. This guide covers all available tool options including callable functions, MCP servers, schemas, and more.

Installation¶

pip install swarms
Overview¶
Swarms provides a comprehensive suite of tool integration methods to enhance your AI agents' capabilities:

Tool Type	Description
Callable Functions	Direct integration of Python functions with proper type hints and comprehensive docstrings for immediate tool functionality
MCP Servers	Model Context Protocol servers enabling distributed tool functionality across multiple services and environments
Tool Schemas	Structured tool definitions that provide standardized interfaces and validation for tool integration
Tool Collections	Pre-built tool packages offering ready-to-use functionality for common use cases
Method 1: Callable Functions¶
Callable functions are the simplest way to add tools to your Swarms agents. They are regular Python functions with type hints and comprehensive docstrings.

Step 1: Define Your Tool Functions¶
Create functions with the following requirements:

Type hints for all parameters and return values

Comprehensive docstrings with Args, Returns, Raises, and Examples sections

Error handling for robust operation

Example: Cryptocurrency Price Tools¶

import json
import requests
from swarms import Agent


def get_coin_price(coin_id: str, vs_currency: str = "usd") -> str:
    """
    Get the current price of a specific cryptocurrency.

    Args:
        coin_id (str): The CoinGecko ID of the cryptocurrency 
                      Examples: 'bitcoin', 'ethereum', 'cardano'
        vs_currency (str, optional): The target currency for price conversion.
                                   Supported: 'usd', 'eur', 'gbp', 'jpy', etc.
                                   Defaults to "usd".

    Returns:
        str: JSON formatted string containing the coin's current price and market data
             including market cap, 24h volume, and price changes

    Raises:
        requests.RequestException: If the API request fails due to network issues
        ValueError: If coin_id is empty or invalid
        TimeoutError: If the request takes longer than 10 seconds

    Example:
        >>> result = get_coin_price("bitcoin", "usd")
        >>> print(result)
        {"bitcoin": {"usd": 45000, "usd_market_cap": 850000000000, ...}}

        >>> result = get_coin_price("ethereum", "eur")
        >>> print(result)
        {"ethereum": {"eur": 3200, "eur_market_cap": 384000000000, ...}}
    """
    try:
        # Validate input parameters
        if not coin_id or not coin_id.strip():
            raise ValueError("coin_id cannot be empty")

        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id.lower().strip(),
            "vs_currencies": vs_currency.lower(),
            "include_market_cap": True,
            "include_24hr_vol": True,
            "include_24hr_change": True,
            "include_last_updated_at": True,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Check if the coin was found
        if not data:
            return json.dumps({
                "error": f"Cryptocurrency '{coin_id}' not found. Please check the coin ID."
            })

        return json.dumps(data, indent=2)

    except requests.RequestException as e:
        return json.dumps({
            "error": f"Failed to fetch price for {coin_id}: {str(e)}",
            "suggestion": "Check your internet connection and try again"
        })
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"})


def get_top_cryptocurrencies(limit: int = 10, vs_currency: str = "usd") -> str:
    """
    Fetch the top cryptocurrencies by market capitalization.

    Args:
        limit (int, optional): Number of coins to retrieve. 
                              Range: 1-250 coins
                              Defaults to 10.
        vs_currency (str, optional): The target currency for price conversion.
                                   Supported: 'usd', 'eur', 'gbp', 'jpy', etc.
                                   Defaults to "usd".

    Returns:
        str: JSON formatted string containing top cryptocurrencies with detailed market data
             including: id, symbol, name, current_price, market_cap, market_cap_rank,
             total_volume, price_change_24h, price_change_7d, last_updated

    Raises:
        requests.RequestException: If the API request fails
        ValueError: If limit is not between 1 and 250

    Example:
        >>> result = get_top_cryptocurrencies(5, "usd")
        >>> print(result)
        [{"id": "bitcoin", "name": "Bitcoin", "current_price": 45000, ...}]

        >>> result = get_top_cryptocurrencies(limit=3, vs_currency="eur")
        >>> print(result)
        [{"id": "bitcoin", "name": "Bitcoin", "current_price": 38000, ...}]
    """
    try:
        # Validate parameters
        if not isinstance(limit, int) or not 1 <= limit <= 250:
            raise ValueError("Limit must be an integer between 1 and 250")

        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": vs_currency.lower(),
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Simplify and structure the data for better readability
        simplified_data = []
        for coin in data:
            simplified_data.append({
                "id": coin.get("id"),
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name"),
                "current_price": coin.get("current_price"),
                "market_cap": coin.get("market_cap"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "total_volume": coin.get("total_volume"),
                "price_change_24h": round(coin.get("price_change_percentage_24h", 0), 2),
                "price_change_7d": round(coin.get("price_change_percentage_7d_in_currency", 0), 2),
                "last_updated": coin.get("last_updated"),
            })

        return json.dumps(simplified_data, indent=2)

    except (requests.RequestException, ValueError) as e:
        return json.dumps({
            "error": f"Failed to fetch top cryptocurrencies: {str(e)}"
        })
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"})


def search_cryptocurrencies(query: str) -> str:
    """
    Search for cryptocurrencies by name or symbol.

    Args:
        query (str): The search term (coin name or symbol)
                    Examples: 'bitcoin', 'btc', 'ethereum', 'eth'
                    Case-insensitive search

    Returns:
        str: JSON formatted string containing search results with coin details
             including: id, name, symbol, market_cap_rank, thumb (icon URL)
             Limited to top 10 results for performance

    Raises:
        requests.RequestException: If the API request fails
        ValueError: If query is empty

    Example:
        >>> result = search_cryptocurrencies("ethereum")
        >>> print(result)
        {"coins": [{"id": "ethereum", "name": "Ethereum", "symbol": "eth", ...}]}

        >>> result = search_cryptocurrencies("btc")
        >>> print(result)
        {"coins": [{"id": "bitcoin", "name": "Bitcoin", "symbol": "btc", ...}]}
    """
    try:
        # Validate input
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        url = "https://api.coingecko.com/api/v3/search"
        params = {"query": query.strip()}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract and format the results
        coins = data.get("coins", [])[:10]  # Limit to top 10 results

        result = {
            "coins": coins,
            "query": query,
            "total_results": len(data.get("coins", [])),
            "showing": min(len(coins), 10)
        }

        return json.dumps(result, indent=2)

    except requests.RequestException as e:
        return json.dumps({
            "error": f'Failed to search for "{query}": {str(e)}'
        })
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"})
Step 2: Configure Your Agent¶
Create an agent with the following key parameters:


# Initialize the agent with cryptocurrency tools
agent = Agent(
    agent_name="Financial-Analysis-Agent",                    # Unique identifier for your agent
    agent_description="Personal finance advisor agent with cryptocurrency market analysis capabilities",
    system_prompt="""You are a personal finance advisor agent with access to real-time 
    cryptocurrency data from CoinGecko. You can help users analyze market trends, check 
    coin prices, find trending cryptocurrencies, and search for specific coins. Always 
    provide accurate, up-to-date information and explain market data in an easy-to-understand way.""",
    max_loops=1,                                              # Number of reasoning loops
    max_tokens=4096,                                          # Maximum response length
    model_name="anthropic/claude-3-opus-20240229",          # LLM model to use
    dynamic_temperature_enabled=True,                         # Enable adaptive creativity
    output_type="all",                                        # Return complete response
    tools=[                                                   # List of callable functions
        get_coin_price,
        get_top_cryptocurrencies,
        search_cryptocurrencies,
    ],
)
Step 3: Use Your Agent¶

# Example usage with different queries
response = agent.run("What are the top 5 cryptocurrencies by market cap?")
print(response)

# Query with specific parameters
response = agent.run("Get the current price of Bitcoin and Ethereum in EUR")
print(response)

# Search functionality
response = agent.run("Search for cryptocurrencies related to 'cardano'")
print(response)
Method 2: MCP (Model Context Protocol) Servers¶
MCP servers provide a standardized way to create distributed tool functionality. They're ideal for:

Reusable tools across multiple agents

Complex tool logic that needs isolation

Third-party tool integration

Scalable architectures

Step 1: Create Your MCP Server¶

from mcp.server.fastmcp import FastMCP
import requests

# Initialize the MCP server with configuration
mcp = FastMCP("OKXCryptoPrice")  # Server name for identification
mcp.settings.port = 8001         # Port for server communication
Step 2: Define MCP Tools¶
Each MCP tool requires the @mcp.tool decorator with specific parameters:


@mcp.tool(
    name="get_okx_crypto_price",                              # Tool identifier (must be unique)
    description="Get the current price and basic information for a given cryptocurrency from OKX exchange.",
)
def get_okx_crypto_price(symbol: str) -> str:
    """
    Get the current price and basic information for a given cryptocurrency using OKX API.

    Args:
        symbol (str): The cryptocurrency trading pair
                     Format: 'BASE-QUOTE' (e.g., 'BTC-USDT', 'ETH-USDT')
                     If only base currency provided, '-USDT' will be appended
                     Case-insensitive input

    Returns:
        str: A formatted string containing:
             - Current price in USDT
             - 24-hour price change percentage
             - Formatted for human readability

    Raises:
        requests.RequestException: If the OKX API request fails
        ValueError: If symbol format is invalid
        ConnectionError: If unable to connect to OKX servers

    Example:
        >>> get_okx_crypto_price('BTC-USDT')
        'Current price of BTC/USDT: $45,000.00\n24h Change: +2.34%'

        >>> get_okx_crypto_price('eth')  # Automatically converts to ETH-USDT
        'Current price of ETH/USDT: $3,200.50\n24h Change: -1.23%'
    """
    try:
        # Input validation and formatting
        if not symbol or not symbol.strip():
            return "Error: Please provide a valid trading pair (e.g., 'BTC-USDT')"

        # Normalize symbol format
        symbol = symbol.upper().strip()
        if not symbol.endswith("-USDT"):
            symbol = f"{symbol}-USDT"

        # OKX API endpoint for ticker information
        url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"

        # Make the API request with timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Check API response status
        if data.get("code") != "0":
            return f"Error: {data.get('msg', 'Unknown error from OKX API')}"

        # Extract ticker data
        ticker_data = data.get("data", [{}])[0]
        if not ticker_data:
            return f"Error: Could not find data for {symbol}. Please verify the trading pair exists."

        # Parse numerical data
        price = float(ticker_data.get("last", 0))
        change_percent = float(ticker_data.get("change24h", 0)) * 100  # Convert to percentage

        # Format response
        base_currency = symbol.split("-")[0]
        change_symbol = "+" if change_percent >= 0 else ""

        return (f"Current price of {base_currency}/USDT: ${price:,.2f}\n"
                f"24h Change: {change_symbol}{change_percent:.2f}%")

    except requests.exceptions.Timeout:
        return "Error: Request timed out. OKX servers may be slow."
    except requests.exceptions.RequestException as e:
        return f"Error fetching OKX data: {str(e)}"
    except (ValueError, KeyError) as e:
        return f"Error parsing OKX response: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@mcp.tool(
    name="get_okx_crypto_volume",                             # Second tool with different functionality
    description="Get the 24-hour trading volume for a given cryptocurrency from OKX exchange.",
)
def get_okx_crypto_volume(symbol: str) -> str:
    """
    Get the 24-hour trading volume for a given cryptocurrency using OKX API.

    Args:
        symbol (str): The cryptocurrency trading pair
                     Format: 'BASE-QUOTE' (e.g., 'BTC-USDT', 'ETH-USDT')
                     If only base currency provided, '-USDT' will be appended
                     Case-insensitive input

    Returns:
        str: A formatted string containing:
             - 24-hour trading volume in the base currency
             - Volume formatted with thousand separators
             - Currency symbol for clarity

    Raises:
        requests.RequestException: If the OKX API request fails
        ValueError: If symbol format is invalid

    Example:
        >>> get_okx_crypto_volume('BTC-USDT')
        '24h Trading Volume for BTC/USDT: 12,345.67 BTC'

        >>> get_okx_crypto_volume('ethereum')  # Converts to ETH-USDT
        '24h Trading Volume for ETH/USDT: 98,765.43 ETH'
    """
    try:
        # Input validation and formatting
        if not symbol or not symbol.strip():
            return "Error: Please provide a valid trading pair (e.g., 'BTC-USDT')"

        # Normalize symbol format
        symbol = symbol.upper().strip()
        if not symbol.endswith("-USDT"):
            symbol = f"{symbol}-USDT"

        # OKX API endpoint
        url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol}"

        # Make API request
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Validate API response
        if data.get("code") != "0":
            return f"Error: {data.get('msg', 'Unknown error from OKX API')}"

        ticker_data = data.get("data", [{}])[0]
        if not ticker_data:
            return f"Error: Could not find data for {symbol}. Please verify the trading pair."

        # Extract volume data
        volume_24h = float(ticker_data.get("vol24h", 0))
        base_currency = symbol.split("-")[0]

        return f"24h Trading Volume for {base_currency}/USDT: {volume_24h:,.2f} {base_currency}"

    except requests.exceptions.RequestException as e:
        return f"Error fetching OKX data: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
Step 3: Start Your MCP Server¶

if __name__ == "__main__":
    # Run the MCP server with SSE (Server-Sent Events) transport
    # Server will be available at http://localhost:8001/mcp
    mcp.run(transport="streamable-http")
Step 4: Connect Agent to MCP Server¶

from swarms import Agent

# Method 2: Using direct URL (simpler for development)
mcp_url = "http://0.0.0.0:8001/mcp"

# Initialize agent with MCP tools
agent = Agent(
    agent_name="Financial-Analysis-Agent",                    # Agent identifier
    agent_description="Personal finance advisor with OKX exchange data access",
    system_prompt="""You are a financial analysis agent with access to real-time 
    cryptocurrency data from OKX exchange. You can check prices, analyze trading volumes, 
    and provide market insights. Always format numerical data clearly and explain 
    market movements in context.""",
    max_loops=1,                                              # Processing loops
    mcp_url=mcp_url,                                         # MCP server connection
    output_type="all",                                        # Complete response format
    # Note: tools are automatically loaded from MCP server
)
Step 5: Use Your MCP-Enabled Agent¶

# The agent automatically discovers and uses tools from the MCP server
response = agent.run(
    "Fetch the price for Bitcoin using the OKX exchange and also get its trading volume"
)
print(response)

# Multiple tool usage
response = agent.run(
    "Compare the prices of BTC, ETH, and ADA on OKX, and show their trading volumes"
)
print(response)
Best Practices¶
Function Design¶
Practice	Description
Type Hints	Always use type hints for all parameters and return values
Docstrings	Write comprehensive docstrings with Args, Returns, Raises, and Examples
Error Handling	Implement proper error handling with specific exception types
Input Validation	Validate input parameters before processing
Data Structure	Return structured data (preferably JSON) for consistency
MCP Server Development¶
Practice	Description
Tool Naming	Use descriptive tool names that clearly indicate functionality
Timeouts	Set appropriate timeouts for external API calls
Error Handling	Implement graceful error handling for network issues
Configuration	Use environment variables for sensitive configuration
Testing	Test tools independently before integration
Agent Configuration¶
Practice	Description
Loop Control	Choose appropriate max_loops based on task complexity
Token Management	Set reasonable token limits to control response length
System Prompts	Write clear system prompts that explain tool capabilities
Agent Naming	Use meaningful agent names for debugging and logging
Tool Integration	Consider tool combinations for comprehensive functionality
Performance Optimization¶
Practice	Description
Data Caching	Cache frequently requested data when possible
Connection Management	Use connection pooling for multiple API calls
Rate Control	Implement rate limiting to respect API constraints
Performance Monitoring	Monitor tool execution times and optimize slow operations
Async Operations	Use async operations for concurrent tool execution when supported
Troubleshooting¶
Common Issues¶
Tool Not Found¶

# Ensure function is in tools list
agent = Agent(
    # ... other config ...
    tools=[your_function_name],  # Function object, not string
)
MCP Connection Failed¶

# Check server status and URL
import requests
response = requests.get("http://localhost:8001/health")  # Health check endpoint
Type Hint Errors¶

# Always specify return types
def my_tool(param: str) -> str:  # Not just -> None
    return "result"
JSON Parsing Issues¶

# Always return valid JSON strings
import json
return json.dumps({"result": data}, indent=2)
December 28, 2025
 
December 2, 2025
 
Kye Gomez