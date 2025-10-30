import difflib
import random
import requests
from typing import Optional, Set, List, Tuple, Dict,Literal
from concurrent.futures import ThreadPoolExecutor, as_completed

from agent.models import Movie, MovieList
from agent.config import TRAKT_CLIENT_ID, TRAKT_CLIENT_SECRET
from agent.logic.services.trakt.filtering import *

# TRAKT_URL settings for all Trakt API calls
TRAKT_URL = "https://api.trakt.tv"
HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-key": TRAKT_CLIENT_ID,
    "trakt-api-version": "2"
}

def query_trakt_movie(
    trakt_id: int = None,
    title: str = None,
    year: int = None,
    include_specific_fields: Optional[Set[str]] = None,
    skip_all_non_included_fields: Optional[bool] = False,
    skip_specific_fields: Optional[Set[str]] = [
        "characters",
        'after_credits_scene',
        'during_credits_scene',
        'music_by',
        'cinematographer',
        'produced_by',
        'written_by',
    ],
) -> dict:
    """
    Fetch extended movie details from Trakt API.

    Returns:
        dict: {
            "status": "no_match" | "match" | "multiple_candidates",
            "movie": Optional[Movie],
            "potential_matches": MovieList,
            "match_score": Optional[float]
        }
    """
    # If searching by title, delegate to search_trakt_movie
    if title and not trakt_id:
        return search_trakt_movie(
            title=title,
            year=year,
        )

    if not trakt_id:
        return {"status": "no_match", "movie": None, "potential_matches": MovieList(), "match_score": 0.0}

    if include_specific_fields is None:
        include_specific_fields = set()

    # Step 1: Fetch core movie data
    core_resp = requests.get(
        f"{TRAKT_URL}/movies/{trakt_id}",
        headers=HEADERS,
        params={"type": "movie", "extended": "full"}
    )
    if core_resp.status_code == 404:
        return {"status": "no_match", "movie": None, "potential_matches": MovieList(), "match_score": 0.0}

    core_resp.raise_for_status()
    core_data = core_resp.json()

    # Step 2: Fetch related info in parallel
    tasks = {
        "people": (f"{TRAKT_URL}/movies/{trakt_id}/people", {}),
    }
    
    if "related" in include_specific_fields:
        tasks["related"] = (f"{TRAKT_URL}/movies/{trakt_id}/related", {}),
    
    # if "comments" in include_specific_fields:
    #     tasks["comments"] = (
    #         f"{TRAKT_URL}/movies/{trakt_id}/comments",
    #         {"params": {"limit": 10, "sort": "likes"}},  # grab up to 50 sorted by likes
    #     )

    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(requests.get, url, headers=HEADERS, **params): name
            for name, (url, params) in tasks.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            response = future.result()
            response.raise_for_status()
            results[key] = response.json()
            
    # # Trim down number of comments
    # if "comments" in results:
    #     # Select 3 at random
    #     comments = results["comments"]
    #     sampled_comments = random.sample(comments, min(3, len(comments)))
    #     results["comments"] = [c["comment"] for c in sampled_comments]

    # Step 3: Map to Movie model
    movie_data = map_trakt_to_movie(
        core_data=core_data,
        people_data=results.get("people"),
        ratings_data=None,
        related_data=results.get("related"),
        # comments_data=results.get("comments"),
        include_fields=include_specific_fields,
        skip_all_non_included_fields=skip_all_non_included_fields,
        skip_specific_fields=skip_specific_fields
    )
    movie_instance = Movie(**movie_data)

    # If looking up by trakt_id directly, we treat it as a perfect match
    return {
        "status": "match",
        "movie": movie_instance,
        "potential_matches": MovieList(),
        "match_score": 1.0
    }

def search_trakt_movie(
    title: str,
    year: int = None,
    max_results_to_check: int = 5
) -> dict:
    """
    Search Trakt movies by title and return:
      - status: "no_match", "match", or "multiple_candidates"
      - movie: Movie instance if one definitive match is found, else None
      - potential_matches: MovieList of top candidates if no single match can be chosen
      - match_score: Confidence score (0–1.0)

    Multiple candidates are returned if several results have very similar high scores.
    """
    
    params = {"query": title, "limit": 10}
    if year is not None:
        params["year"] = year
    # if genres:
    #     params["genres"] = ",".join(genres)
    # if certifications:
    #     params["certifications"] = ",".join(certifications)
    # if networks:
    #     params["countries"] = ",".join(networks)
        
    search_resp = requests.get(
        f"{TRAKT_URL}/search/movie",
        headers=HEADERS,
        params=params,
    )
    search_resp.raise_for_status()
    results = search_resp.json()
    
    print("search results is", results, "\n------")

    if not results:
        return {"status": "no_match", "movie": None, "potential_matches": MovieList(), "match_score": 0.0}

    # -- Score top N results
    scored_results = []
    for result in results[:max_results_to_check]:
        movie = result.get("movie")
        if not movie or "title" not in movie:
            continue
        ratio = difflib.SequenceMatcher(None, title.lower(), movie["title"].lower()).ratio()
        scored_results.append((ratio, movie))

    if not scored_results:
        return {"status": "no_match", "movie": None, "potential_matches": MovieList(), "match_score": 0.0}

    # -- Sort by best match ratio
    scored_results.sort(key=lambda x: x[0], reverse=True)
    best_ratio, best_movie = scored_results[0]

    # -- Check for multiple very close matches
    close_matches = [m for r, m in scored_results if r >= (best_ratio - 0.05) and r >= 0.8]  # within 5% & high score
    if len(close_matches) > 1:        
        # Match by year if provided and only one entry aligns
        matched_by_year = False
        if year is not None:
            year_matches = [m for m in close_matches if m.get("year") == year]
            
            if len(year_matches) == 1:
                best_movie = year_matches[0]
                best_ratio = difflib.SequenceMatcher(
                    None,
                    title.lower(),
                    best_movie["title"].lower()
                ).ratio()
                matched_by_year = True
        
        if not matched_by_year:
            movie_list = MovieList(
                movies=[
                    query_trakt_movie(
                        trakt_id=m["ids"]["trakt"],
                        include_specific_fields=["title", "year", "trakt_id", "runtime", "director", "cast"],
                        skip_all_non_included_fields=True
                    )["movie"] for m in close_matches[:5]
                ]
            )
            
            return {
                "status": "multiple_candidates",
                "movie": None,
                "potential_matches": movie_list,
                "match_score": 1.0
            }
        

    # -- Select single best match
    trakt_id = best_movie["ids"].get("trakt")
    if not trakt_id:
        return {"status": "no_match", "movie": None, "potential_matches": [], "match_score": None}

    movie_instance = query_trakt_movie(trakt_id=trakt_id)["movie"]

    return {
        "status": "match",
        "movie": movie_instance,
        "potential_matches": [],
        "match_score": best_ratio
    }


def query_top_trakt_movies(
    num: int = 3,
    list_type: Literal[
        "trending",
        "popular",
        "anticipated",
        "watched",
        "boxoffice",
    ] = "trending",
) -> MovieList:
    """
    Fetch a list of top movies from Trakt API and map them to MovieList.

    Args:
        num: Number of movies to fetch (max 10).
        list_type: Type of movie list to fetch (trending, popular, etc.).

    Returns:
        MovieList: A Pydantic MovieList model containing a list of Movies.
    """
    num = min(num, 10)

    endpoint_map = {
        "trending": "movies/trending",
        "popular": "movies/popular",
        "anticipated": "movies/anticipated",
        "watched": "movies/watched/weekly",
        "boxoffice": "movies/boxoffice",
    }

    endpoint = endpoint_map[list_type]
    response = requests.get(f"{TRAKT_URL}/{endpoint}?extended=full", headers=HEADERS)
    response.raise_for_status()

    movies: List[Movie] = []

    # Reduced info if fetching many movies (e.g. >=8)
    reduced = num >= 8

    for entry in response.json()[:num]:
        movie_data = entry.get("movie", entry)
        
        print("-----------movie_data is---------------")
        print(movie_data)

        # Map only core fields + trakt_rating
        mapped = map_trakt_to_movie(
            core_data=movie_data,
            include_fields={
                "title",
                "description",
                "runtime",
                "release_date",
                "genres",
                "director",
                "cast",
                "trailer",
                "tagline",
                "subgenres",
                "trakt_rating",
                "country",
                "age_rating",
                
            },
            skip_specific_fields = {
                "after_credits_scene",
                "during_credits_scene",
                "year",
                "trakt_votes",
            }
        )
        
        print("--------------------mapped is-------------------")
        print(mapped)
        print("\n\n\n\n")
        

        # Fetch cast & director info separately for each movie
        credits_resp = requests.get(
            f"{TRAKT_URL}/movies/{movie_data['ids']['trakt']}/people", headers=HEADERS
        )
        credits_resp.raise_for_status()
        credits = credits_resp.json()

        # Use a helper for top cast (3 or 5 depending on reduced)
        top_cast_count = 3 if reduced else 5
        # TODO: FIND BETTER WAY TO CULL CAST TO CORE
        mapped["cast"] = [c["person"]["name"] for c in credits.get("cast", [])[:top_cast_count]]

        if not reduced:
            mapped["description"] = movie_data.get("overview", "")

            # Pull from directing crew
            directing_crew = credits.get("crew", {}).get("directing", [])
            director = next(
                (c["person"]["name"] for c in directing_crew if c.get("job") == "Director" and "person" in c),
                None
            )
            mapped["director"] = director

        movies.append(Movie(**mapped))

    return MovieList(movies=movies)


def query_related_movies(
    num: int = 3,
    limit: int = 10,
    title: Optional[str] = None,
    year: int = None,
    trakt_id: Optional[int] = None,
) -> dict:
    """
    Fetch a list of related movies from Trakt for a given movie.

    If `trakt_id` is not provided, the function will look up the movie by `title`.

    Args:
        num: Number of related movies to fetch (max 10).
        title: Title of the movie to find related movies for (used if trakt_id is not provided).
        trakt_id: Trakt ID of the movie.

    Returns:
        dict: {
            "status": "success" | "candidate_title_not_found" | "could_not_choose_candidate",
            "movie": Movie object for the original movie (or None),
            "similar_movies": MovieList containing related movies
        }
    """
    num = min(num, limit)
    search_movie = None

    # --- Resolve trakt_id from title if needed ---
    if not trakt_id:
        queried_movie = query_trakt_movie(title=title, year=year) if title else None
        if not queried_movie:
            return {
                "status": "no_match",
                "message": f"No match in trakt.tv could be found for the provided title '{title}'",
                "search_movie": None,
                "similar_movies": MovieList(),
            }

        if queried_movie['status'] == "match":
            trakt_id = queried_movie['movie'].trakt_id
            title = queried_movie['movie'].title
            year = queried_movie['movie'].year
            search_movie = queried_movie['movie']
        else:
            return {
                "status": "search_movie_has_many_matches",
                "message": f"Too many potential matches for search movie. Are they any of these? Try again with more specific title",
                "search_movie": None,
                "model_instance": queried_movie.get('potential_matches'),
            }

    # --- Fetch related movies from Trakt API ---
    related_resp = requests.get(
        f"{TRAKT_URL}/movies/{trakt_id}/related",
        headers=HEADERS,
        params={"limit": num},
    )
    related_resp.raise_for_status()
    related_movies_json = related_resp.json()

    related_movies_list = [
        Movie(
            title=m.get("title"),
            original_title=m.get("title"),
            year=m.get("year"),
            trakt_id=m["ids"]["trakt"],
            genres=m.get("genres", []),
            tagline=m.get("tagline"),
            description=m.get("overview"),
            runtime=m.get("runtime"),
            trailer=m.get("trailer"),
        )
        for m in related_movies_json[:num]
    ]
    
    print("related_movies_list is", related_movies_list)

    similar_movies = MovieList(movies=related_movies_list)

    return {
        "status": "success" if related_movies_list else "no_related_movies",
        "message": "Found list of movies similar to search_movie!",
        "search_movie": search_movie,
        "model_instance": similar_movies,
    }