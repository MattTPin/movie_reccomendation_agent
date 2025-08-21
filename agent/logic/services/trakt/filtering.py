import requests
from typing import Any, Optional, Set, List, Tuple, Dict

from agent.models import Movie, MovieList

BASE = "https://api.trakt.tv"

def map_trakt_to_movie(
    core_data: dict,
    people_data: Optional[dict] = None,
    ratings_data: Optional[dict] = None,
    comments_data: Optional[dict] = None,
    related_data: Optional[list] = None,
    include_fields: Optional[Set[str]] = None,
    skip_all_non_included_fields: Optional[bool] = False,
    skip_specific_fields: Optional[Set[str]] = None,
) -> dict:
    """
    Map Trakt API responses into a dictionary compatible with the Movie Pydantic model.

    Args:
        core_data (dict): Main movie metadata from /movies/{id}.
        people_data (dict, optional): Credits info from /movies/{id}/people.
        ratings_data (dict, optional): Ratings info from /movies/{id}/ratings.
        comments_data (dict, optional): Comments info from /movies/{id}/comments
        related_data (list, optional): List of related movies from /movies/{id}/related.
        include_fields (set, optional): Fields to include even if normally excluded.
        skip_specific_fields (set, optional): Fields to exclude from output unless in include_fields.

    Returns:
        dict: Parsed movie data matching Movie schema.
    """
    
    include_fields = include_fields or set()
    skip_specific_fields = skip_specific_fields or set()

    def include(field_name: str) -> bool:
        # Bool to override all defaults and only include explicit field names
        if skip_all_non_included_fields:
            return field_name in include_fields
        # Always include if explicitly whitelisted
        if field_name in include_fields:
            return True
        # Exclude if blacklisted and not explicitly included
        if field_name in skip_specific_fields:
            return False
        # Default include
        return True

    mapped = {
        "title": core_data.get("title"),
        "year": core_data.get("year"),
    }

    if include("original_title"):
        mapped["original_title"] = core_data.get("original_title")

    if include("tagline"):
        mapped["tagline"] = core_data.get("tagline")

    if include("runtime"):
        mapped["runtime"] = core_data.get("runtime")

    if include("genres"):
        genres = core_data.get("genres")
        mapped["genres"] = genres if isinstance(genres, list) else None

    if include("subgenres"):
        subgenres = core_data.get("subgenres")
        mapped["subgenres"] = subgenres if isinstance(subgenres, list) else None

    if include("description"):
        mapped["description"] = core_data.get("overview")

    if include("release_date"):
        mapped["release_date"] = core_data.get("released")

    if include("country"):
        mapped["country"] = core_data.get("country")

    if include("age_rating"):
        mapped["age_rating"] = core_data.get("certification")

    if include("after_credits_scene"):
        mapped["after_credits_scene"] = core_data.get("after_credits")

    if include("during_credits_scene"):
        mapped["during_credits_scene"] = core_data.get("during_credits")

    if include("trakt_id"):
        ids = core_data.get("ids", {})
        mapped["trakt_id"] = ids.get("trakt")
        
    if include("trailer"):
        mapped["trailer"] = core_data.get("trailer")

    if include("trakt_rating"):
        mapped["trakt_rating"] = core_data.get("rating")

    if include("trakt_votes"):
        mapped["trakt_votes"] = core_data.get("votes")

    if include("cast") and people_data:
        cast = people_data.get("cast", [])
        cast = [c["person"]["name"] for c in cast if "person" in c]
        mapped["cast"] = cast[:4]

    if include("characters") and people_data:
        cast = people_data.get("cast", [])
        mapped["characters"] = [c.get("character") for c in cast if c.get("character")]

    if include("director") and people_data:
        crew = people_data.get("crew", {}).get("directing", [])
        mapped["director"] = next(
            (c["person"]["name"] for c in crew if c.get("job") == "Director" and "person" in c),
            None
        )
        
    if include("comments") and comments_data:
        mapped["comments"] = [
            c["comment"] for c in comments_data if "comment" in c
        ]

    if include("music_by") and people_data:
        sound = people_data.get("crew", {}).get("sound", [])
        mapped["music_by"] = next(
            (c["person"]["name"] for c in sound if c.get("job") == "Original Music Composer" and "person" in c),
            None
        )

    if include("cinematographer") and people_data:
        camera = people_data.get("crew", {}).get("camera", [])
        mapped["cinematographer"] = next(
            (c["person"]["name"] for c in camera if c.get("job") == "Director of Photography" and "person" in c),
            None
        )

    if include("written_by") and people_data:
        writing = people_data.get("crew", {}).get("writing", [])
        writers = [c["person"]["name"] for c in writing if "person" in c]
        mapped["written_by"] = writers or None

    if include("produced_by") and people_data:
        production = people_data.get("crew", {}).get("production", [])
        producers = [c["person"]["name"] for c in production if c.get("job") == "Producer" and "person" in c]
        mapped["produced_by"] = producers or None

    if include("related") and related_data:
        related_titles = [movie.get("title") for movie in related_data if movie.get("title")]
        mapped["related"] = related_titles

    # Stubbed fields not provided by Trakt, for future enrichment via other APIs
    # unsupported = [
    #     "franchise", "production_companies", "budget", "revenue",
    #     "box_office_domestic", "box_office_worldwide", "streaming_on",
    #     "rotten_tomatoes_score", "metacritic_score", "letterboxd_score",
    #     "imdb_score", "cinemascore"
    # ]

    return mapped



def get_top_cast(cast_list: List[Dict], top_n: int = 3) -> List[str]:
    """
    Determine the top cast members (lead actors) from a Trakt cast list.
    Assumes the list is ordered by billing.

    Args:
        cast_list: list of cast entries (each has 'person' dict with 'name').
        top_n: maximum number of top actors to return.

    Returns:
        A list of the first `top_n` actor names, or fewer if not available.
    """
    return [entry["person"]["name"] for entry in cast_list[:top_n]]

def get_release_date(trakt_id: int, region: str) -> Optional[str]:
    """
    Fetch the release date for a specific region using the Trakt releases endpoint.

    Args:
        trakt_id: Trakt numeric movie ID.
        region: two-letter country code (ISO 3166-1 alpha-2).

    Returns:
        The release date string for that region, or None if not found.
    """
    url = f"{BASE}/movies/{trakt_id}/releases"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    releases = resp.json().get("releases", [])
    for rel in releases:
        if rel.get("country") == region:
            return rel.get("release_date")
    # fallback to first available
    return releases[0].get("release_date") if releases else None