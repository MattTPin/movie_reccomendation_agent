# router.py
import json
from typing import List, Dict

from agent.logic.actions.get_actions import (
    GetTrending,
    GetMovieDetails,
    GetRelatedMovies,
    GetUserList
)
from agent.logic.actions.post_actions import (
    AddOrRemoveFromWatchList
)
from agent.models import (
    generate_system_prompt_from_model_instance,
)
from agent.logic.llm import invoke_claude


# The dictionary of known Claude actions and their corresponding functions
# Action flow steps...
#     - Immediate
#     - Follow-up
#     - Final


action_dict = {
    "GetTrending": {
        "description": "Get current popular movies.",
        "immediate_args": {
            "num": "int (opt) default = 5"
        },
        "immediate_arg_notes": None,
        "follow_up_func": None,
        "follow_up_args": {},
        "final_func": GetTrending.get_trending,
        "final_arg_notes": None,
    },
    "GetDetails": {
        "description": "Get info on specific movie.",
        "immediate_args": {
            "title": "(opt)",
            "year": "(opt)",
            "trakt_id": "(opt)",
        },
        "immediate_arg_notes": None, # "One of 'title' or 'trakt_id' required.",
        "follow_up_func": GetMovieDetails.get_movie_details,
        "follow_up_args": {
            "title": "str (opt)",
            "trakt_id": "int (opt)"
        },
        "final_func": GetMovieDetails.get_movie_details,
        "final_arg_notes": None, # "One of 'title' or 'trakt_id' required.",
        "final_arg_notes": None,
    },
    "GetSimilar": {
        "description": "Get related movies to provided search movie.",
        "immediate_args": {
            "title": "(opt)",
            "year": "(opt)",
            # "trakt_id": "(opt)",
            "num": "(opt)",
        },
        "immediate_arg_notes": "One of 'title' or 'trakt_id' required.",
        "follow_up_func": None,
        "follow_up_args": None,
        "final_func": GetRelatedMovies.get_related_list,
        "final_arg_notes": None, # "One of 'title' or 'trakt_id' required.",
        "final_arg_notes": None,
    },
    "GetUserList": {
        "description": "get list of movies (i.e. user's watchlist)",
        "immediate_args": {
            "list_type": "(req)",
            "limit": "(opt)",
        },
        "immediate_arg_notes": None,
        "follow_up_args": {
            "page": "int (optional, default 1)",
            "genres": "List[str] (optional) - filter",
            "subgenres": "List[str] (optional) - filter",
            "streaming_on": "List[str] (optional) - streaming services filter",
            "country": "str (optional) - filter",
            "runtime_range": "Tuple[int,int] (optional) - min/max runtime mins",
            "year_range": "Tuple[int,int] (optional) - min/max release year",
            "score_cutoff": "float (optional) - minimum trakt_rating",
            "sort_by": "Literal[None,'trakt_rating','runtime','year'] (optional)"
        },
        "follow_up_func": None,
        "final_func": GetUserList.get_user_list,
        "final_arg_notes": "If a user asks for more list entries, add the previous number of entries to the current page and use that as the page value."
    },
    "AddOrRemoveFromWatchList": {
        "description": "Update user watchlist for a single movie",
        "immediate_args": {
            "title": "(req)",
            # "trakt_id": "(opt)",
            "mode": "(opt)",
        },
        "immediate_arg_notes": None,
        "follow_up_args": None,
        "follow_up_func": None,
        "final_func": AddOrRemoveFromWatchList.add_or_remove_from_watchlist,
        "final_arg_notes": None
    },
}

default_arg_desc= {
    "title (str)": "best guess movie title (**never** include year). If unknown to you rely on user input",
    "year (int)": "movie release year",
    # "trakt_id (int)": "trakt.tv movie id. Only include if already exists in previous message. Never fill if you don't know it.",
    "num (int)": "num movies",
    "limit (int)": "max movies, max=15",
    "list_type (str)": "one of ['watchlist','collection','ratings','history']",
    "mode (str)": "one of ['add' or 'remove']",
}

def build_action_router_prompt():
    """
    Build a lightweight system prompt listing only action names + short description for initial routing.
    This reduces prompt size for action selection.
    """
    action_lines = []
    for name, config in action_dict.items():
        # Short summary: action name + immediate args only
        line = f"- {name}"
        desc = config.get("description")
        if config.get("description"):
            line += f": {desc}"
            
        if config.get("immediate_args"):
            args_summary = ", ".join(config["immediate_args"].keys())
            line += f" (args: {args_summary})"
        action_lines.append(line)

    actions_text = "\n".join(action_lines)

    return f"""
    You are a router for a movie recommendation agent. Your task is to select **one action** to perform based on the last two messages, prioritizing the **most recent message**.

    You **must respond only** with a single JSON object with two keys:
    - "action" (string): the name of the chosen action
    - "args" (object): arguments for the action (empty object if no arguments)

    Rules:
    1. Never include any extra text, commentary, or explanations.
    2. Never embed the JSON inside natural language.
    3. Always ensure a valid JSON object is returned — no partial JSON or explanations.
    4. Only use natural language **if and only if you cannot determine an action** from the user's most recent message.
    5. You may receive "HIDDEN MEMORY" JSONs. These are for your reference. Do not pass them in the response text.
    6. Never make up trakt.tv ID numbers. Only retrieve them from previous messages if they match a target movie.
    
    These are your actions:

    {actions_text}
    
    Arg details:
    {str(default_arg_desc)}
    """.strip()
    #     If you cannot map the user request to any action, forget about actions
    # and reply with plain text.
    


SYSTEM_PROMPT = build_action_router_prompt()


def route(history: list[dict]) -> dict:
    """
    Route user input to an appropriate action and manage follow-up queries.

    Steps:
    1. Run lightweight router to pick action + immediate args.
    2. Run follow_up_func if defined (may return success, secondary_query_required, or error).
    3. If secondary_query_required → silent fill follow_up_args → retry final_func.
    4. Return structured output with args notes.
    """
    user_prompt = history[-1]["content"] if history and history[-1]["role"] == "user" else ""

    # -- Router picks action + args
    router_resp = invoke_claude(
        prompt=user_prompt,
        system_prompt=SYSTEM_PROMPT,
        history=history
    )
    router_text = router_resp["content"][0]["text"]

    try:
        router_json = json.loads(router_text)
        action = router_json["action"]
        selected_args = router_json.get("args", {}) or {}
    except Exception:
        return {"fallback": router_text}

    if action not in action_dict:
        return {"fallback": f"Unknown action '{action}'. Got: {router_text}"}

    print(f"SELECTED ACTION '{action}'")

    config = action_dict[action]
    follow_up_args = config.get("follow_up_args", {})
    follow_up_func = config.get("follow_up_func")
    final_func = config["final_func"]

    # -- Call follow_up_func if present
    if follow_up_func:
        action_result = follow_up_func(**selected_args) if selected_args else follow_up_func()

        print("follow_up action_result is", action_result)

        status = action_result.get("status")
        if status == "secondary_query_required":
            # 3. Silent query for missing args
            filled_args = silent_query_for_follow_up_args(
                action_name=action,
                # pass model instance of initial call as "prompt"
                user_prompt=action_result.get("model_instance").model_dump_json(exclude_unset=True),
                current_args=selected_args,
                follow_up_args=follow_up_args,
                base_system_prompt=action_result.get("action_prompt", "")
            )
            selected_args.update(filled_args)

            # Retry final func with updated args
            action_result = final_func(**selected_args)
            status = action_result.get("status")

        if status == "error":
            # Skip LLM entirely — pass error back to user
            return {"status": "error", "prompt": action_result.get("prompt")}

        elif status == "success":
            return _build_success_response(action, action_result, config)

        else:
            return {"status": "error", "prompt": f"Unknown status '{status}' from follow_up_func."}

    # -- If no follow-up func → go straight to final_func
    action_result = final_func(**selected_args) if selected_args else final_func()
    print("non-followup action_result is", action_result)
    return _build_success_response(action, action_result, config)


def silent_query_for_follow_up_args(
    action_name: str,
    user_prompt: str,
    current_args: dict,
    follow_up_args: dict,
    base_system_prompt: str
) -> dict:
    """
    Perform a hidden LLM query to fill follow-up arguments for an action.
    Prepends specific instructions to the action's normal system prompt.
    """
    if not follow_up_args:
        return {}

    extra_instructions = f"""
        Return **only** a JSON with keys:
            - "action" str: {action_name}
            - "args" dict: arguments for function (empty if none)
        Fill (or replace) the args as you see fit: {', '.join(follow_up_args.keys())}.",
    """

    combined_system_prompt = base_system_prompt.strip() + "\n\n" + extra_instructions

    response = invoke_claude(
        prompt=user_prompt,
        system_prompt=combined_system_prompt,
        silent_mode=True
    )

    try:
        filled_args = json.loads(response["content"][0]["text"])
        return filled_args
    except Exception:
        return {arg: None for arg in follow_up_args}


def _build_success_response(
    action: str,
    action_result,
    config: dict
) -> dict:
    """Helper to build the final 'success' response structure."""
    action_prompt = action_result.get('action_prompt')
    
    # Optional: attach argument notes if provided
    if config.get("immediate_arg_notes"):
        action_prompt += f"\narg notes: {config.get('immediate_arg_notes')}"
    if config.get("final_arg_notes"):
        action_prompt += f"\narg notes: {config.get('final_arg_notes')}"

    print(f"action_result is ({type(action_result)})")
    print(action_result)

    return {
        "status": "success",
        "action": action,
        "action_json": action_result['model_instance'].model_dump_json(exclude_unset=True),
        "action_prompt": action_prompt
    }