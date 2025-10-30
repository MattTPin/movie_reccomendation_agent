# test_dice_agent.py
import json
from typing import Any, List
from langchain_core.tools import tool  # or BaseTool depending your version
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_agent

from agent.llm.llm_client import LLMClient
from agent.llm.llm_agent import LLMAgent
from agent.test_tools.dice import dice


# --- Initialize LLM (Claude/Anthropic) ---
llm_client = LLMClient(provider="anthropic")
llm_client.initialize_client()

# --- Define tool using @tool decorator ---
@tool
def dice_roll() -> int:
    """Rolls a 6-sided dice and returns the result."""
    return dice()

tools = [dice_roll]

system_prompt = (
    "You are an agent. You can respond normally or call tools.\n"
    "If using a tool, respond exactly in JSON: {\"tool\": <tool_name>, \"args\": <args_dict>}.\n"
)

# --- Create the agent ---
dice_agent_runnable = LLMAgent(
    llm_client=llm_client,
    system_prompt=system_prompt,
    tools=tools
)
