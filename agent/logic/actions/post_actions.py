# post_actions.py
from typing import Literal, List

from agent.models import (
    TraktListActionResult,
)
from agent.logic.services.trakt.trakt_lists import (
    update_trakt_list
)


class AddOrRemoveFromWatchList:
    post_action_prompt_template = f"""
    You are a helpful movie agent. You just helped a user perform an action where they added
    (or removed) movies from their trakt.tv. Respond in natural language based on the result
    of the action based on the info in the json. Do not show the json or allude to it existing
    in your response. Do not show any "hidden memory".
    
    After reporting on the success of the action ask if there's any other ways you can be of assistance
    in finding movies or adding them to their watchlist.
    """

    @staticmethod
    def add_or_remove_from_watchlist(
        title: str = None,
        trakt_id: int = None,
        year: int = None,
        mode: Literal["add", "remove"] = "add",
        target_list: Literal["watchlist", "collection", "ratings", "history", "comments"] = "watchlist",
    ) -> dict:
        """
        Adds or removes a movie from the Trakt watchlist.

        Returns a dictionary matching the format of GetMovieDetails:
            {
                "status": "success" | "error",
                "model_instance": TraktListActionResult,
                "action_prompt": str
            }
        """
        if not title and not trakt_id:
            return {
                "status": "error",
                "model_instance": TraktListActionResult(
                    action_name=f"{mode}_to_list",
                    target_list="watchlist",
                    action_success=False,
                    successfully_updated_titles=[],
                    non_updated_error_titles=["No title or trakt_id provided"],
                    message="No title or trakt_id provided.",
                ),
                "action_prompt": "Tell the user no action can be performed without a movie title.",
            }
            
        if title and year:
            title = f"{title} ({str(year)})"

        # Call the update_trakt_list function
        result: TraktListActionResult = update_trakt_list(
            movies=[{"title": title, "trakt_id": trakt_id}],
            target_list="watchlist",
            mode=mode,
        )
        
        print(f"result is ({type(result)})", result)

        # Build response dict in same shape as GetMovieDetails
        return {
            "status": "success",
            "model_instance": result,
            "action_prompt": AddOrRemoveFromWatchList.post_action_prompt_template,
        }