import httpx
import webbrowser
import requests
from typing import Optional, Set, List, Tuple, Dict,Literal
from concurrent.futures import ThreadPoolExecutor, as_completed

from agent.models import Movie, MovieList, TraktActionResult
from agent.config import (
    TRAKT_URL,
    TRAKT_CLIENT_ID,
    TRAKT_ACCESS_TOKEN,
    TRAKT_CLIENT_SECRET
)
from agent.logic.services.trakt.filtering import *
from agent.logic.services.trakt.get_movies import query_trakt_movie

# Settings for Trakt API calls
TRAKT_URL = "https://api.trakt.tv"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TRAKT_ACCESS_TOKEN}",
    "trakt-api-key": TRAKT_CLIENT_ID,
    "trakt-api-version": "2"
}

def update_trakt_list(
    movies: List[Dict] = None,  # [{"title": "...", "trakt_id": ..., "rating": ..., "comment": ...}]
    title: str = None,
    trakt_id: int = None,
    target_list: Literal["watchlist", "collection", "ratings", "history", "comments"] = "watchlist",
    mode: Literal["add", "remove"] = "add"
) -> TraktActionResult:
    """
    Add or remove one or more movies from a given Trakt list.

    Args:
        movies: Optional list of movie dicts with title/trakt_id (and rating/comment if relevant).
        title: Title of a single movie (used if movies not provided).
        trakt_id: Trakt ID of a single movie (used if movies not provided).
        target_list: Which Trakt list to target (watchlist, collection, ratings, history, comments).
        mode: "add" or "remove".

    Returns:
        TraktActionResult summarizing success/failure, updated titles, error titles, messages, and API response.
    """
    action_name = f"{mode}_to_list"
    added_or_removed_titles: List[str] = []
    failed_titles: List[str] = []
    trakt_movies_payload: List[Dict] = []
    per_movie_messages: List[str] = []

    # 1) Normalize input into a movies list
    if not movies:
        movies = [{"title": title, "trakt_id": trakt_id}]

    # 2) Resolve trakt_id for each movie (via title lookup if needed)
    for movie in movies:
        trakt_id = movie.get("trakt_id")
        title = movie.get("title")

        if not trakt_id:
            resolved = query_trakt_movie(title=title) if title else None
            if not resolved:
                failed_titles.append(title or "Unknown title")
                per_movie_messages.append(f"❌ Could not find '{title or 'Unknown title'}' on Trakt.")
                continue

            if resolved['status'] == "match":
                trakt_id = resolved['movie'].trakt_id
                movie["title"] = resolved['movie'].title
                movie["trakt_id"] = trakt_id
            else:
                return resolved  # error passthrough from query_trakt_movie

        # Build Trakt movie payload
        trakt_movie_data = {"ids": {"trakt": trakt_id}}
        if target_list == "ratings" and movie.get("rating") is not None:
            trakt_movie_data["rating"] = movie["rating"]
        if target_list == "comments" and movie.get("comment") is not None:
            trakt_movie_data["comment"] = movie["comment"]

        trakt_movies_payload.append(trakt_movie_data)

    if not trakt_movies_payload:
        return TraktActionResult(
            action_name=action_name,
            target_list=target_list,
            action_success=False,
            successfully_updated_titles=[],
            non_updated_error_titles=failed_titles,
            message="No valid movies could be processed for this action."
        )

    # 3) POST to Trakt API
    endpoint = (
        f"{TRAKT_URL}/sync/{target_list}"
        if mode == "add"
        else f"{TRAKT_URL}/sync/remove"
    )
    post_resp = requests.post(endpoint, headers=HEADERS, json={"movies": trakt_movies_payload})
    post_resp.raise_for_status()
    resp_json = post_resp.json()

    # 4) Normalize response into consistent lists
    def ensure_list(maybe):
        """Ensure Trakt response part is always a list of dicts."""
        if isinstance(maybe, list):
            return maybe
        return []  # if int, None, or unexpected

    added_key = "added" if mode == "add" else "deleted"
    added_movies_list = ensure_list(resp_json.get(added_key, {}).get("movies"))
    existing_movies = ensure_list(resp_json.get("existing", {}).get("movies"))
    not_found_movies = ensure_list(resp_json.get("not_found", {}).get("movies"))

    # 5) Per-movie result evaluation
    for movie in movies:
        title = movie["title"]
        trakt_id = movie["trakt_id"]

        # Success check
        if trakt_id in [m.get("trakt") for m in added_movies_list if isinstance(m, dict)]:
            added_or_removed_titles.append(title)
            verb = "added to" if mode == "add" else "removed from"
            per_movie_messages.append(f"✅ Successfully {verb} {target_list}: '{title}'.")
        else:
            if title in failed_titles:
                continue

            if mode == "add":
                if trakt_id in [m.get("trakt") for m in existing_movies if isinstance(m, dict)]:
                    per_movie_messages.append(f"ℹ '{title}' is already in your {target_list}. No action taken.")
                else:
                    per_movie_messages.append(f"❌ Failed to add '{title}' to {target_list} for an unknown reason.")
            else:  # remove
                if trakt_id in [m.get("trakt") for m in not_found_movies if isinstance(m, dict)]:
                    per_movie_messages.append(f"ℹ '{title}' was not found in your {target_list}, so it couldn't be removed.")
                else:
                    per_movie_messages.append(f"❌ Failed to remove '{title}' from {target_list} for an unknown reason.")

            failed_titles.append(title)

    # 6) Build final result
    success = len(added_or_removed_titles) > 0
    final_message = "\n".join(per_movie_messages)

    return TraktActionResult(
        action_name=action_name,
        target_list=target_list,
        action_success=success,
        successfully_updated_titles=added_or_removed_titles,
        non_updated_error_titles=failed_titles,
        message=final_message,
        details=resp_json
    )
    

def query_user_trakt_list(
    list_type: Literal["watchlist", "collection", "ratings", "history", "comments"] = "watchlist",
    limit: int = 10,
    page: int = 1,                                # pagination support
    genres: Optional[List[str]] = None,
    subgenres: Optional[List[str]] = None,
    streaming_on: Optional[List[str]] = None,     # e.g., ["Netflix", "Hulu"]
    country: Optional[str] = None,                # filter by production country
    runtime_range: Optional[Tuple[int, int]] = None,  # (min_minutes, max_minutes)
    year_range: Optional[Tuple[int, int]] = None,     # (min_year, max_year)
    score_cutoff: Optional[float] = None,         # trakt_rating threshold
    sort_by: Optional[str] = None                 # e.g., "trakt_rating", "runtime", "release_date"
) -> MovieList:
    """
    Fetch a list of movies from a user's Trakt list (watchlist, collection, ratings, etc.)
    and map them to MovieList, with optional filtering and sorting.

    Notes:
        - Uses `extended=min` to maximize returned results — `extended=full` includes more fields
          but can limit throughput for very large lists.
        - Filters are applied directly to the raw API JSON before making any extra requests.
        - People-based filtering (cast, director) is not supported here to avoid per-movie
          requests that would slow down large list queries.
        - Supports pagination via the `page` parameter.

    Args:
        list_type: User-specific Trakt list to fetch.
        limit: Max number of movies to fetch per page (Trakt allows up to 100; default 10).
        page: Page number for pagination (starts at 1).
        genres: List of genre terms to filter by (case-insensitive).
        subgenres: List of subgenre terms to filter by.
        streaming_on: List of streaming services to filter by.
        country: Filter by country.
        runtime_range: Tuple of (min, max) runtime in minutes.
        year_range: Tuple of (min, max) release year.
        score_cutoff: Minimum trakt_rating to include.
        sort_by: Field to sort results by.

    Returns:
        MovieList: Pydantic model containing the user's movies after filtering/sorting.
    """
    limit = min(limit, 100)  # API limit safeguard

    # -----------------------------
    # 1) Determine endpoint
    # -----------------------------
    endpoint_map = {
        "watchlist": "sync/watchlist/movies",
        "collection": "sync/collection/movies",
        "ratings": "sync/ratings/movies",
        "history": "sync/history/movies",
        "comments": "users/me/comments/movies"
    }

    endpoint = endpoint_map[list_type]    
    response = requests.get(
        f"{BASE}/{endpoint}?extended=full&limit={limit}&page={page}", 
        headers=HEADERS
    )
    response.raise_for_status()
    data = response.json()
    
    # 2) Apply filters
    def raw_matches_filters(entry: dict) -> bool:
        movie_data = entry.get("movie", entry)

        # Genres & subgenres
        if genres:
            if not any(g.lower() in [mg.lower() for mg in movie_data.get("genres", [])] for g in genres):
                return False
        if subgenres:
            if not any(sg.lower() in [ms.lower() for ms in movie_data.get("subgenres", [])] for sg in subgenres):
                return False

        # Streaming availability (if included in extended data)
        if streaming_on:
            if not any(s.lower() in [ms.lower() for ms in movie_data.get("streaming_on", [])] for s in streaming_on):
                return False

        # Country
        if country:
            if not movie_data.get("country") or country.lower() not in movie_data["country"].lower():
                return False

        # Runtime
        if runtime_range:
            min_runtime, max_runtime = runtime_range
            runtime = movie_data.get("runtime") or 0
            if runtime < min_runtime or runtime > max_runtime:
                return False

        # Release year
        if year_range:
            if movie_data.get("year"):
                year = int(movie_data["year"])
                min_year, max_year = year_range
                if year < min_year or year > max_year:
                    return False

        # Score cutoff
        if score_cutoff:
            if movie_data.get("rating") is None or movie_data["rating"] < score_cutoff:
                return False

        return True

    # Filter before doing extra requests
    filtered_data = [entry for entry in data if raw_matches_filters(entry)]
    
    # 3) Convert returned movies to Pydantic Movie models
    movies: List[Movie] = []
    for entry in filtered_data[:limit]:
        movie_data = entry.get("movie", entry)  # unwrap if needed

        if len(filtered_data) <= 10:
            # Get more info if we have shorter list
            include_fields={
                "title",
                "description",
                "runtime",
                "release_date",
                "genres",
                "trailer",
                "tagline",
                "trakt_rating",
                "country",
                "age_rating",
                "subgenres",
            }
            skip_specific_fields={
                "after_credits_scene",
                "during_credits_scene",
                "year",
                "trakt_votes",
                "director",
                "cast",
            }
        else:
            # For long lists keep info lean
            include_fields={
                "title",
                "runtime",
                "genres",
                "tagline",
                "trakt_rating",
            }
            skip_specific_fields={
                "after_credits_scene",
                "during_credits_scene",
                "year",
                "trakt_votes",
                "country",
                "age_rating",
                "director",
                "cast",
                "trailer",
            }
        
        # Always try to include the sort_by field if specified
        if sort_by in Movie.model_fields:
            include_fields.add(sort_by)
            
        # Map core fields + trakt_rating
        mapped = map_trakt_to_movie(
            core_data=movie_data,
            include_fields=include_fields,
            skip_specific_fields=skip_specific_fields
        )
        
        # Add cast if list is short enough
        if len(filtered_data) < 5:
            # Fetch cast & director info separately for each movie
            credits_resp = requests.get(
                f"{BASE}/movies/{movie_data['ids']['trakt']}/people", headers=HEADERS
            )
            credits_resp.raise_for_status()
            credits = credits_resp.json()

            # Use a helper for top cas
            top_cast_count = 5
            # TODO: FIND BETTER WAY TO CULL CAST TO CORE
            mapped["cast"] = [c["person"]["name"] for c in credits.get("cast", [])[:top_cast_count]]

            mapped["description"] = movie_data.get("overview", "")

            # Pull from directing crew
            directing_crew = credits.get("crew", {}).get("directing", [])
            director = next(
                (c["person"]["name"] for c in directing_crew if c.get("job") == "Director" and "person" in c),
                None
            )
            mapped["director"] = director
        

        if list_type == "ratings" and "rating" in entry:
            mapped["user_rating"] = entry["rating"]

        movies.append(Movie(**mapped))


    # -----------------------------
    # 4) Apply sorting
    # -----------------------------
    if sort_by:
        try:
            movies.sort(key=lambda m: getattr(m, sort_by) or 0, reverse=True)
        except AttributeError:
            pass  # ignore invalid sort_by fields

    # -----------------------------
    # 5) Return Pydantic MovieList
    # -----------------------------
    return MovieList(movies=movies)