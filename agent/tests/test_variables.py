from typing import Literal
from langchain_core.messages import AIMessage
import json
import random
import uuid


expected_test_responses = {
    "isolate_vehicle_description": {
        "success": "SUCCESS MESSAGE",
        "failed": {"description": "No description found."},
        "unexpected_json": {"vehicle_info": "It's a great car!"},
        "not_json": "It's an OK car!"
    }
}

def create_mock_llm_response(
    function_name: Literal["isolate_vehicle_description"],
    provider: Literal["anthropic", "openai", "mistral"],
    response_type: Literal["success", "failed", "unexpected_json", "not_json"] = "success"
) -> AIMessage:
    """
    Create a simulated AIMessage to mimic LLM responses with realistic structure per provider.
    """
    try:
        content_value = expected_test_responses[function_name][response_type]
    except KeyError:
        content_value = "Generic response"

    # Convert dict responses to JSON string; leave strings as-is
    content = json.dumps(content_value) if isinstance(content_value, dict) else content_value

    # --- token counts ---
    input_tokens = random.randint(50, 150)
    output_tokens = random.randint(20, 100)
    total_tokens = input_tokens + output_tokens

    # --- build response metadata depending on provider ---
    if provider == "anthropic":
        response_metadata = {
            "id": str(uuid.uuid4()),
            "model": "claude-3-5-haiku-20241022",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        }
    elif provider == "openai":
        response_metadata = {
            "id": str(uuid.uuid4()),
            "model": "gpt-4.1-mini",
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        }
    elif provider == "mistral":
        response_metadata = {
            "id": str(uuid.uuid4()),
            "model": "mistral-7b-v2",
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        }
    else:
        raise ValueError(f"Unknown llm provider: {provider}")

    return AIMessage(
        content=content,
        additional_kwargs={},
        response_metadata=response_metadata,
        id=str(uuid.uuid4()),
        usage_metadata={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        }
    )