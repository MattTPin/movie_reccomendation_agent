# llm_client.py
import os
from typing import Optional, Literal, Any, Dict, List
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import create_agent

from agent.errors import (
    LLMConfigError,
    LLMInitializationError
)
from agent.test_tools.dice import dice

from agent.llm.llm_client import LLMClient

SUPPORTED_PROVIDERS = ["anthropic"]
load_dotenv()
from langchain_core.tools import BaseTool
from collections.abc import Awaitable, Callable, Sequence

class LLMAgent:
    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str = None,
        tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    ):
        self.agent = create_agent(
            model=llm_client.client,
            tools=tools,
            system_prompt=system_prompt,
        )

    def _normalize_messages_for_agent(self, messages):
        """
        Convert HumanMessage/AIMessage/SystemMessage or dict-like items
        into the simple dict format agent.invoke expects:
        {"role": "user" | "assistant" | "system", "content": "..."}
        """
        normalized = []
        for m in messages:
            # If it's already a dict-like mapping with role/content, pass through
            if isinstance(m, dict) and "content" in m and "role" in m:
                normalized.append({"role": m["role"], "content": m["content"]})
                continue

            # langchain_core message classes -> map to role
            if isinstance(m, HumanMessage):
                normalized.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                normalized.append({"role": "assistant", "content": m.content})
            elif isinstance(m, SystemMessage):
                normalized.append({"role": "system", "content": m.content})
            else:
                # Fallback: coerce to string and call it a user message
                normalized.append({"role": "user", "content": str(m)})
        return normalized


    def _parse_agent_result(self, result: dict):
        """
        Extract the latest AI response message and token usage from a LangChain agent result.
        Works with Anthropic or OpenAI backends.
        """
        messages = result.get("messages", [])
        if not messages:
            return "", {}

        # Find the last AIMessage (skip ToolMessages)
        final_ai_msg = None
        for msg in reversed(messages):
            from langchain_core.messages import AIMessage
            if isinstance(msg, AIMessage):
                final_ai_msg = msg
                break

        if final_ai_msg is None:
            return "", {}

        # Extract content
        content = final_ai_msg.content
        if isinstance(content, list):
            # Anthropic sometimes wraps in list of dicts
            content = " ".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in content
            )

        # Extract token usage
        usage = {}
        if hasattr(final_ai_msg, "usage_metadata"):
            usage_meta = final_ai_msg.usage_metadata
            usage = {
                "input_tokens": usage_meta.get("input_tokens"),
                "output_tokens": usage_meta.get("output_tokens"),
                "total_tokens": usage_meta.get("total_tokens"),
            }
        elif final_ai_msg.response_metadata.get("usage"):
            usage = final_ai_msg.response_metadata.get("usage")

        return content.strip(), usage

    def invoke(self, messages: list) -> AIMessage:
        # history should be list of HumanMessage / AIMessage
        # Build input dict for invocation
        agent_messages = self._normalize_messages_for_agent(messages)
        
        agent_response = self.agent.invoke({
            "messages": agent_messages
        })
        
        result_message, tokens_used = self._parse_agent_result(agent_response)
        
        # The result will likely contain structured return — might need to adapt output parsing
        # For simplicity, assume result is a string answer
        return AIMessage(content=str(result_message))