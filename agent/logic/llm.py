# llm.py

import boto3
import json
import os

from agent.models import Person  # or wherever your model is
from agent.config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BEDROCK_MODEL_ID

boto3_client = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def invoke_claude(
    prompt: str,
    system_prompt: str = None,
    history: list[dict] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    silent_mode: bool = False
) -> dict:
    """
    Invoke Claude through Amazon Bedrock.

    Args:
        prompt (str): The current user prompt.
        system_prompt (str, optional): System-level instructions.
        history (list[dict], optional): Prior messages, list of {"role": "user|assistant", "content": str}.
        max_tokens (int, optional): Maximum tokens to sample.
        temperature (float, optional): Sampling temperature.
        silent_mode (bool, optional): If True, do not include history. Defaults to False.

    Returns:
        dict: Full Claude response body.
    """
    print("----------INVOKING Claude WITH...----------: ")
    print("prompt", type(prompt), prompt)
    print("system_prompt", type(system_prompt), system_prompt)
    print("history", type(history), history)
    print("silent_mode", silent_mode)
    print("-------------------------------------------")

    messages = []

    if prompt:
        messages.append({"role": "user", "content": prompt})

    # Only include history if not in silent mode
    if history and not silent_mode:
        filtered_history = []
        
        # Include only most recent "hidden" message
        hidden_seen = False

        # traverse in reverse to keep most recent
        for m in reversed(history):
            if m.get("role") == "hidden" and not hidden_seen:
                filtered_history.append({**m, "role": "assistant"})  # swap hidden -> assistant
                hidden_seen = True
            elif m.get("role") in ("user", "assistant"):
                filtered_history.append(m)
            if len(filtered_history) >= 6:  # 5 recent + 1 hidden
                break

        # reverse back to original order
        messages.extend(reversed(filtered_history))

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if system_prompt:
        body["system"] = system_prompt

    response = boto3_client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
    )

    response_body = json.loads(response["body"].read().decode("utf-8"))
    print("CLAUDE RESPONSE BODY IS", response_body)
    return response_body