# post_actions.py
from typing import Literal, List

from agent.models import (
    Movie,
    MovieList,
    TraktActionResult,
    generate_system_prompt_from_model_instance
)
from agent.logic.services.tmdb import (
    _get_genre_map,
    get_tmdb_movie,
    query_tmdb_trending_movies
)
from agent.logic.services.trakt.get_movies import (
    query_top_trakt_movies,
    search_trakt_movie,
    query_trakt_movie,
)
from agent.logic.services.trakt.trakt_lists import (
    update_trakt_list
)


class AddOrRemoveFromWatchList:
    post_action_prompt_template = f"""
    You are a helpful movie agent. You just helped a user perform an action where they added
    (or removed) movies from their trakt.tv
    
    The status of this action and its success is summarized in the provided JSON.
    
    After reporting on the success of the action if there's any other ways you can be of assistance
    in finding movies or adding them to their watchlist.
    """

    @staticmethod
    def add_or_remove_from_watchlist(
        title: str = None,
        trakt_id: int = None,
        mode: Literal["add", "remove"] = "add",
        target_list: Literal["watchlist", "collection", "ratings", "history", "comments"] = "watchlist",
    ) -> dict:
        """
        Adds or removes a movie from the Trakt watchlist.

        Returns a dictionary matching the format of GetMovieDetails:
            {
                "status": "success" | "error",
                "model_instance": TraktActionResult,
                "action_prompt": str
            }
        """
        if not title and not trakt_id:
            return {
                "status": "error",
                "model_instance": TraktActionResult(
                    action_name=f"{mode}_to_list",
                    target_list="watchlist",
                    action_success=False,
                    successfully_updated_titles=[],
                    non_updated_error_titles=["No title or trakt_id provided"],
                    message="No title or trakt_id provided.",
                ),
                "action_prompt": "Tell the user no action can be performed without a movie title.",
            }

        # Call the update_trakt_list function
        result: TraktActionResult = update_trakt_list(
            movies=[{"title": title, "trakt_id": trakt_id}],
            target_list="watchlist",
            mode=mode,
        )

        # Build response dict in same shape as GetMovieDetails
        return {
            "status": "success",
            "model_instance": result,
            "action_prompt": AddOrRemoveFromWatchList.post_action_prompt_template,
        }