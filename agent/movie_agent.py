# movie_agent.py
from typing import List, Dict, Optional
import json

from langchain_core.tools import tool  # or BaseTool depending your version
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_agent

from agent.llm.llm_client import LLMClient
from agent.llm.llm_agent import LLMAgent

from agent.logic.actions.get_actions import (
    GetTrending,
    GetMovieDetails,
    GetRelatedMovies,
    GetUserList
)
from agent.logic.actions.post_actions import (
    AddOrRemoveFromWatchList
)

SYSTEM_PROMPT = """
You are a movie recommendation routing assistant.
Decide which action to take based on user queries about movies,
streaming services, or watchlists. Use the available tools to find data.
If the user asks something unrelated, respond in natural language.
Use the action argument descriptions to select valid arguments.
"""

# --- Initialize LLM (Claude/Anthropic) ---
llm_client = LLMClient(provider="anthropic")
llm_client.initialize_client()

# --- Define tool using @tool decorator ---

# --- Default argument descriptions ---
default_arg_desc = {
    "title (str)": "best guess movie title (**never** include year). If unknown, rely on user input",
    "year (int)": "movie release year",
    "num (int)": "num movies",
    "limit (int)": "max movies, max=15",
    "list_type (str)": "one of ['watchlist','collection','ratings','history']",
    "mode (str)": "one of ['add' or 'remove']",
}

# --- Tool: GetTrending ---
@tool
def get_trending(num: int = 5) -> dict:
    """
    Get current popular movies.

    Args:
        num: number of movies to return (optional, default=5)
    
    Returns:
        dict: {
            "status": "success",
            "action": "GetTrending",
            "action_json": raw movie data,
            "action_prompt": formatted prompt/message
        }
    """
    # Call the existing final_func
    trending_result = GetTrending.get_trending(num=num)
    
    return {
        "action_name" : "GetTrending",
        "movie_list" : trending_result["movie_list"].model_dump_json(exclude_unset=True),
        "action_prompt": trending_result['action_prompt'], 
        "status": "success"
    }


# --- Tool: GetDetails ---
@tool
def get_movie_details(
    title: Optional[str] = None,
    year: Optional[int] = None,
    trakt_id: Optional[int] = None
) -> dict:
    """
    Get info on a specific movie.

    Args:
        title: best guess movie title (**never** include year). Optional.
        year: release year. Optional.
        trakt_id: trakt.tv movie ID. Optional. Use only if known.
    Notes:
        At least one of 'title' or 'trakt_id' should be provided. Provide only
        `trakt_id` IF you see one in previous messages that matches the user's
        request.
    
    Returns:
        dict: movie details
    """
    movie_details = GetMovieDetails.get_movie_details(
        title=title,
        year=year,
        trakt_id=trakt_id
    )
    
    return {
        "action_name" : "GetTrending",
        "model_instance" : movie_details["model_instance"].model_dump_json(exclude_unset=True),
        "action_prompt": movie_details['action_prompt'], 
        "status": movie_details['status']
    }

    
# --- Tool: GetSimilar ---
@tool
def get_similar_movies(
    title: Optional[str] = None,
    year: Optional[int] = None,
    num: Optional[int] = 3,
) -> dict:
    """
    Get related movies to the provided search movie.

    Args:
        title: The title of the movie to find related movies for. Optional.
        year: Release year of the movie. Optional.
        num: Number of related movies to return. Optional.

    Notes:
        At least one of 'title' or 'trakt_id' should be provided in the original system.
        Since trakt_id is not included here, rely on title/year if available.

    Returns:
        dict: {
            "status": "success",
            "action_name": "GetSimilar",
            "model_instance": JSON of related movies,
            "action_prompt": prompt for LLM to format the output
        }
    """
    # Call the original final_func
    action_result = GetRelatedMovies.get_related_list(
        title=title,
        year=year,
        num=num,
    )

    final_prompt = {
        "status": "success",
        "action_name": "GetSimilar",
        "model_instance": action_result["model_instance"].model_dump_json(exclude_unset=True),
        "action_prompt": action_result.get("action_prompt", ""),
    }

    # Wrap in the generic tool-compatible response
    return final_prompt


# --- Tool: GetUserList ---
@tool
def get_user_list(
    page: Optional[int] = 1,
) -> dict:
    """
    Get a list of movies from a user's watchlist.

    Args:
        page: Page number for pagination (optional, default=1).

    Notes:
        If a user asks for more list entries, add the previous number of entries
        to the current page and use that as the page value.

    Returns:
        dict: {
            "status": "success",
            "action_name": "GetUserList",
            "model_instance": JSON of movies,
            "action_prompt": prompt for LLM to format the output
        }
    """
    # Call the original final_func
    action_result = GetUserList.get_user_list(
        list_type="watchlist",
        page=page,
    )

    # Wrap in generic tool-compatible response
    return {
        "status": "success",
        "action_name": "GetUserList",
        "model_instance": action_result["model_instance"].model_dump_json(exclude_unset=True),
        "action_prompt": action_result.get("action_prompt", ""),
    }


# --- Tool: AddOrRemoveFromWatchList ---
@tool
def update_watchlist(
    mode: Optional[str] = "add",
    title: Optional[str] = None,
    trakt_id: Optional[int] = None,
) -> dict:
    """
    Update a user's watchlist for a single movie.

    Args:
        title: Optional title of the movie to add or remove.
        mode: Operation mode, either 'add' or 'remove' (optional, default='add').
        trakt_id: Optional Trakt.tv movie ID to uniquely identify the movie.

    Notes:
        At least one of 'title' or 'trakt_id' should be provided. Provide only
        `trakt_id` IF you see one in previous messages that matches the user's
        request.

    Returns:
        dict: {
            "status": "success",
            "action_name": "AddOrRemoveFromWatchList",
            "model_instance": JSON of updated watchlist or result,
            "action_prompt": prompt for LLM to format the output
        }
    """
    # Call the original final_func
    action_result = AddOrRemoveFromWatchList.add_or_remove_from_watchlist(
        title=title,
        mode=mode,
        trakt_id=trakt_id
    )

    return {
        "status": "success",
        "action_name": "AddOrRemoveFromWatchList",
        "model_instance": action_result["model_instance"].model_dump_json(exclude_unset=True),
        "action_prompt": action_result.get("action_prompt", ""),
    }
    

tools = [
    get_trending,
    get_movie_details,
    get_similar_movies,
    get_user_list,
    update_watchlist,
]

system_prompt = (
    "You are an agent. You can respond normally or call tools.\n"
    "If using a tool, respond exactly in JSON: {\"tool\": <tool_name>, \"args\": <args_dict>}.\n"
)

# --- Create the agent ---
movie_agent_runnable = LLMAgent(
    llm_client=llm_client,
    system_prompt=system_prompt,
    tools=tools
)
